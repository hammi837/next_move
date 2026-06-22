import redis
import json
from typing import Optional, Any, Callable
from datetime import timedelta, datetime
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class InMemoryCache:
    """Simple in-process cache used as fallback when Redis is unavailable."""

    def __init__(self):
        self._store: dict = {}  # key -> (value, expires_at)

    def get(self, key: str) -> Optional[Any]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expires_at = entry
        if expires_at and datetime.utcnow() > expires_at:
            del self._store[key]
            return None
        return value

    def set(self, key: str, value: Any, ex: int = 3600) -> bool:
        expires_at = datetime.utcnow() + timedelta(seconds=ex) if ex else None
        self._store[key] = (value, expires_at)
        return True

    def delete(self, key: str) -> bool:
        self._store.pop(key, None)
        return True


class CacheService:
    """Redis cache service with automatic in-memory fallback."""

    def __init__(self):
        self._client = None
        self._fallback = InMemoryCache()
        self._redis_available = True  # optimistic; will flip on first failure

    def _get_client(self) -> redis.Redis:
        """Lazy-connect to Redis. Returns None if Redis is unavailable."""
        if not self._redis_available:
            return None
        if self._client is None:
            try:
                self._client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=settings.REDIS_DB,
                    password=settings.REDIS_PASSWORD if settings.REDIS_PASSWORD else None,
                    decode_responses=True,
                    socket_connect_timeout=5,
                    socket_keepalive=True,
                )
                self._client.ping()
                logger.info("✅ Redis connection successful")
            except redis.ConnectionError as e:
                logger.warning(f"⚠️ Redis unavailable – falling back to in-memory cache: {e}")
                self._client = None
                self._redis_available = False
        return self._client

    def _mark_redis_dead(self, e: Exception):
        """Mark Redis as unavailable so we stop hammering it."""
        if self._redis_available:
            logger.warning(f"⚠️ Redis unavailable – switching to in-memory cache: {e}")
            self._redis_available = False
            self._client = None

    # ── Core operations ──────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = self._get_client()
        if client is None:
            return self._fallback.get(key)
        try:
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            self._mark_redis_dead(e)
            return self._fallback.get(key)

    def set(self, key: str, value: Any, ex: int = 3600) -> bool:
        """Set value in cache with expiration (seconds)."""
        client = self._get_client()
        if client is None:
            return self._fallback.set(key, value, ex)
        try:
            client.setex(key, timedelta(seconds=ex), json.dumps(value, default=str))
            return True
        except Exception as e:
            self._mark_redis_dead(e)
            return self._fallback.set(key, value, ex)

    def delete(self, key: str) -> bool:
        """Delete a cache key."""
        client = self._get_client()
        if client is None:
            return self._fallback.delete(key)
        try:
            client.delete(key)
            return True
        except Exception as e:
            self._mark_redis_dead(e)
            return self._fallback.delete(key)

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching a pattern."""
        client = self._get_client()
        if client is None:
            return 0
        try:
            keys = client.keys(pattern)
            if keys:
                return client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Cache delete pattern error for {pattern}: {e}")
            return 0

    def get_or_set(self, key: str, fetch_func: Callable, ex: int = 3600) -> Any:
        """Get from cache or call *fetch_func*, store, and return."""
        cached = self.get(key)
        if cached is not None:
            logger.debug(f"Cache HIT: {key}")
            return cached

        logger.debug(f"Cache MISS: {key}")
        data = fetch_func()
        if data is not None:
            self.set(key, data, ex)
        return data

    def clear_all(self) -> bool:
        """Flush the entire Redis DB (use with caution)."""
        client = self._get_client()
        if client is None:
            return False
        try:
            client.flushdb()
            logger.info("Cache cleared")
            return True
        except Exception as e:
            logger.error(f"Failed to clear cache: {e}")
            return False


# Singleton
cache_service = CacheService()
