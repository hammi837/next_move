"""
WebSocket endpoints — real-time price updates & alert notifications.
"""

import asyncio
import json
import logging
import uuid
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()


class _Hub:
    """In-process WebSocket hub."""

    def __init__(self):
        self._conns: Dict[str, WebSocket] = {}       # conn_id → ws
        self._subs:  Dict[str, Set[str]]  = {}       # symbol  → {conn_ids}
        self._users: Dict[int, Set[str]]  = {}       # user_id → {conn_ids}

    async def connect(self, ws: WebSocket,
                      symbol: str = None,
                      user_id: int = None) -> str:
        await ws.accept()
        cid = str(uuid.uuid4())[:8]
        self._conns[cid] = ws
        if symbol:
            self._subs.setdefault(symbol.upper(), set()).add(cid)
        if user_id:
            self._users.setdefault(user_id, set()).add(cid)
        return cid

    def disconnect(self, cid: str):
        self._conns.pop(cid, None)
        for s in self._subs.values():
            s.discard(cid)
        for u in self._users.values():
            u.discard(cid)

    async def broadcast_symbol(self, symbol: str, data: dict):
        dead = []
        for cid in list(self._subs.get(symbol.upper(), [])):
            ws = self._conns.get(cid)
            if ws:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(cid)
        for cid in dead:
            self.disconnect(cid)

    async def send_to_user(self, user_id: int, data: dict):
        dead = []
        for cid in list(self._users.get(user_id, [])):
            ws = self._conns.get(cid)
            if ws:
                try:
                    await ws.send_json(data)
                except Exception:
                    dead.append(cid)
        for cid in dead:
            self.disconnect(cid)


hub = _Hub()


# ── Live price feed ───────────────────────────────────────────────────────

@router.websocket("/ws/prices/{symbol}")
async def live_prices(ws: WebSocket, symbol: str):
    """
    Stream latest price for `symbol` every 5 seconds from the DB.
    Client can send { "type": "ping" } to keep alive.
    """
    cid = await hub.connect(ws, symbol=symbol)
    try:
        while True:
            # Non-blocking receive with timeout so we can push prices
            try:
                raw  = await asyncio.wait_for(ws.receive_text(), timeout=5.0)
                msg  = json.loads(raw)
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                pass
            except Exception:
                break

            # Push latest price from DB
            try:
                from app.db.database import SessionLocal
                from app.db.models   import MarketMetadata
                db   = SessionLocal()
                meta = db.query(MarketMetadata).filter(
                    MarketMetadata.symbol == symbol.upper()
                ).first()
                db.close()
                if meta and meta.last_price:
                    await ws.send_json({
                        "type":   "price",
                        "symbol": symbol.upper(),
                        "price":  meta.last_price,
                        "ts":     meta.last_update.isoformat() if meta.last_update else None,
                    })
            except Exception as e:
                logger.warning(f"WS price push error: {e}")

    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(cid)


# ── User alerts feed ──────────────────────────────────────────────────────

@router.websocket("/ws/alerts/{user_id}")
async def user_alerts(ws: WebSocket, user_id: int):
    """
    Stream triggered alerts for `user_id`.
    """
    cid = await hub.connect(ws, user_id=user_id)
    await ws.send_json({"type": "connected", "user_id": user_id})
    try:
        while True:
            try:
                raw = await asyncio.wait_for(ws.receive_text(), timeout=30.0)
                msg = json.loads(raw)
                if msg.get("type") == "ping":
                    await ws.send_json({"type": "pong"})
            except asyncio.TimeoutError:
                # Send heartbeat
                await ws.send_json({"type": "heartbeat"})
            except Exception:
                break
    except WebSocketDisconnect:
        pass
    finally:
        hub.disconnect(cid)


# ── Public broadcast helper (called from background tasks) ─────────────────

async def broadcast_alert_to_user(user_id: int, alert_data: dict):
    await hub.send_to_user(user_id, {"type": "alert", **alert_data})
