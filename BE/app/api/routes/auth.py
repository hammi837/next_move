"""
Authentication routes — register, login, me, refresh (sync stack).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from datetime import datetime

from app.db.database import get_db
from app.services.auth_service import auth_service

router   = APIRouter()
security = HTTPBearer(auto_error=False)


def _current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
):
    if not credentials:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = auth_service.get_user_from_token(db, credentials.credentials)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


# ── Register ──────────────────────────────────────────────────────────────

@router.post("/register", status_code=201)
def register(payload: dict, db: Session = Depends(get_db)):
    """
    Body: { username, email, password, full_name? }
    """
    try:
        user = auth_service.register(
            db,
            username  = payload.get("username", ""),
            email     = payload.get("email", ""),
            password  = payload.get("password", ""),
            full_name = payload.get("full_name", ""),
        )
        token = auth_service.issue_token(user)
        return {
            "access_token": token,
            "token_type":   "bearer",
            "user": {
                "id":        user.id,
                "username":  user.username,
                "email":     user.email,
                "full_name": user.full_name,
                "role":      user.role.value,
            },
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── Login ─────────────────────────────────────────────────────────────────

@router.post("/login")
def login(payload: dict, db: Session = Depends(get_db)):
    """
    Body: { username, password }   (username can be email too)
    """
    user = auth_service.login(
        db,
        username = payload.get("username", ""),
        password = payload.get("password", ""),
    )
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return {
        "access_token": auth_service.issue_token(user),
        "token_type":   "bearer",
        "user": {
            "id":        user.id,
            "username":  user.username,
            "email":     user.email,
            "full_name": user.full_name,
            "role":      user.role.value,
        },
    }


# ── Current user ──────────────────────────────────────────────────────────

@router.get("/me")
def get_me(user=Depends(_current_user)):
    return {
        "id":          user.id,
        "username":    user.username,
        "email":       user.email,
        "full_name":   user.full_name,
        "role":        user.role.value,
        "preferences": user.preferences or {},
        "last_login":  user.last_login.isoformat() if user.last_login else None,
    }


# ── Update preferences ────────────────────────────────────────────────────

@router.put("/preferences")
def update_preferences(
    payload: dict,
    user=Depends(_current_user),
    db: Session = Depends(get_db),
):
    prefs = dict(user.preferences or {})
    prefs.update(payload)
    user.preferences = prefs
    db.commit()
    return {"status": "ok", "preferences": user.preferences}


# ── Refresh ───────────────────────────────────────────────────────────────

@router.post("/refresh")
def refresh(user=Depends(_current_user)):
    return {
        "access_token": auth_service.issue_token(user),
        "token_type":   "bearer",
    }
