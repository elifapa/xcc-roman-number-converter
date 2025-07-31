import redis
import json
import structlog
from typing import Optional, Any, Protocol
import time
import os
# from contextlib import contextmanager

from xcc_roman_converter.config import configure_logging

# Configure logging
configure_logging()
logger = structlog.get_logger()

class BaseCache(Protocol):
    def __init__(self, host: str, port: int, db):
        ...
    def is_connected(self) -> bool:
        ...
    def get(self) -> Optional[Any]:
        ...
    def set(self) -> Optional[Any]:
        ...


class RedisCache:
    def __init__(self, host: str = os.getenv("CACHE_HOST"), port: int = os.getenv("CACHE_PORT"), db: int = 0, 
                 decode_responses: bool = True):
        """
        Initialize Redis cache connection.
        
        Args:
            host: Redis server host
            port: Redis server port
            db: Redis database number
            decode_responses: Whether to decode responses to strings
        """
        try:
            self.client = redis.Redis(
                host=host, 
                port=port, 
                db=db, 
                decode_responses=decode_responses,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.debug("Redis connection established 🟢", host=host, port=port)
        except redis.ConnectionError as e:
            logger.warning("Redis connection failed, caching disabled", error=str(e))
            self.client = None
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available."""
        return self.client is not None
    
    def get(self, key: str, suppress_log: bool = False) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected():
            return None
        
        try:
            start = time.perf_counter()
            value = self.client.get(key)
            end = time.perf_counter()
            if value:
                if not suppress_log:
                    logger.info("Cache hit ✅", duration_ms = round((end - start) * 1000, 5), key=key, value=value)
                return json.loads(value)
            logger.info("Cache miss 🙅", key=key)
            return None
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error("Cache get error ❌", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any) -> bool:
        """Set value in cache."""
        if not self.is_connected():
            return False
        
        try:
            if value:
                serialized_value = json.dumps(value)
                result = self.client.set(key, serialized_value)
                logger.info("Cache set ✅", key=key, value=value)
                return result
            else:
                logger.warning("Attempted to set None value in cache", key=key)
                return False
        except (redis.RedisError, json.JSONEncodeError) as e:
            logger.error("Cache set error ❌", key=key, error=str(e))
            return False
        
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        if not self.is_connected():
            return False
        
        try:
            result = self.client.delete(key)
            logger.debug("Cache delete", key=key)
            return bool(result)
        except redis.RedisError as e:
            logger.error("Cache delete error ❌", key=key, error=str(e))
            return False
    
    def clear(self) -> bool:
        """Clear all cache entries."""
        if not self.is_connected():
            return False
        
        try:
            result = self.client.flushdb()
            logger.info("Cache cleared ✅")
            return result
        except redis.RedisError as e:
            logger.error("Cache clear error ❌", error=str(e))
            return False
    
    # @contextmanager
    # def get_or_set(self, key: str, expire: Optional[int] = None):
    #     """Context manager for get-or-set pattern."""
    #     cached_value = self.get(key)
    #     if cached_value is not None:
    #         yield cached_value, True  # (value, was_cached)
    #     else:
    #         # Yield None to indicate cache miss, let caller compute value
    #         computed_value = yield None, False
    #         if computed_value is not None:
    #             self.set(key, computed_value, expire)
    #         yield computed_value, False
    

# Global cache instance
cache = RedisCache()