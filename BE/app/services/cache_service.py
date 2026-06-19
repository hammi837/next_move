import redis
import json
from typing import Optional, Any, Callable
from datetime import timedelta
import logging

from app.config import settings

logger = logging.getLogger(__name__)


class CacheService:
    """Redis cache service for market data caching."""

    def __init__(self):
        self._client = None

    def _get_client(self) -> redis.Redis:
        """Lazy-connect to Redis."""
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
                logger.warning(f"⚠️ Redis unavailable – caching disabled: {e}")
                self._client = None
        return self._client

    # ── Core operations ──────────────────────────────────────────────────

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        client = self._get_client()
        if client is None:
            return None
        try:
            data = client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache get error for key {key}: {e}")
            return None

    def set(self, key: str, value: Any, ex: int = 3600) -> bool:
        """Set value in cache with expiration (seconds)."""
        client = self._get_client()
        if client is None:
            return False
        try:
            client.setex(key, timedelta(seconds=ex), json.dumps(value, default=str))
            return True
        except Exception as e:
            logger.warning(f"Cache set error for key {key}: {e}")
            return False

    def delete(self, key: str) -> bool:
        """Delete a cache key."""
        client = self._get_client()
        if client is None:
            return False
        try:
            client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Cache delete error for key {key}: {e}")
            return False

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
