import redis
import json
import structlog
from typing import Optional, Any, Protocol
import time
import os

from xcc_roman_converter.config import configure_logging

# Configure logging
configure_logging()
logger = structlog.get_logger()

class CacheProtocol(Protocol):
    """Protocol defining the cache interface."""
    def is_connected(self) -> bool:
        ...
    def get(self, key: str, suppress_log: bool = False) -> Optional[Any]:
        ...
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        ...
    def delete(self, key: str) -> bool:
        ...
    def clear(self) -> bool:
        ...

# class NoOpCache:
#     """A no-operation cache that does nothing - used when Redis is disabled."""
    
#     def __init__(self):
#         logger.debug("NoOpCache initialized - caching disabled")
    
#     def is_connected(self) -> bool:
#         return False
    
#     def get(self, key: str, suppress_log: bool = False) -> Optional[Any]:
#         return None
    
#     def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
#         return False
    
#     def delete(self, key: str) -> bool:
#         return False
    
#     def clear(self) -> bool:
#         logger.debug("NoOpCache clear called - no-op")
#         return False
    
#     def get_info(self) -> dict:
#         return {}
    
#     def get_keys(self, pattern: str = "*") -> list:
#         return []
    
#     def get_key_count(self) -> int:
#         return 0

class RedisCache:
    """Redis-based cache implementation."""
    
    def __init__(self, host: str = os.getenv("CACHE_HOST", "localhost"), 
                 port: int = os.getenv("CACHE_PORT", 6379), 
                 db: int = 0):
        """
        Initialize Redis cache connection.
        
        Args:
            host: Redis server host (default: localhost)
            port: Redis server port (default: 6379)
            db: Redis database number (default: 0)
            decode_responses: Whether to decode responses to strings
            enabled: Whether caching is enabled
        """
        self.client = None
        self.host = host or "localhost"
        self.port = port or 6379
        self.db = db
        
        if not os.getenv("CACHE_ENABLED", "False").lower() in ("true", "1", "yes", "on"):
            logger.debug("Redis caching is disabled")
            return
        
        self._connect()
    
    def _connect(self):
        """Establish connection to Redis."""
        try:
            self.client = redis.Redis(
                host=self.host, 
                port=self.port, 
                db=self.db, 
                decode_responses=True,
                socket_connect_timeout=5,
                socket_timeout=5
            )
            # Test connection
            self.client.ping()
            logger.info("Redis connection established 🟢", host=self.host, port=self.port, db=self.db)
        except redis.ConnectionError as e:
            logger.warning("Redis connection failed 🔴", host=self.host, port=self.port, error=str(e))
            self.client = None
        except Exception as e:
            logger.error("Unexpected error during Redis connection", error=str(e))
            self.client = None
    
    def reconnect(self) -> bool:
        """Attempt to reconnect to Redis."""
        logger.info("Attempting to reconnect to Redis...", host=self.host, port=self.port)
        self._connect()
        return self.is_connected()
    
    def is_connected(self) -> bool:
        """Check if Redis is connected and available."""
        if self.client is None:
            return False
        
        try:
            self.client.ping()
            return True
        except redis.ConnectionError:
            logger.debug("Redis connection lost")
            self.client = None
            return False
        except Exception as e:
            logger.debug("Error checking Redis connection", error=str(e))
            return False
    
    def get(self, key: str, suppress_log: bool = False) -> Optional[Any]:
        """Get value from cache."""
        if not self.is_connected():
            return None
        
        try:
            start = time.perf_counter()
            value = self.client.get(key)
            end = time.perf_counter()
            
            if value:
                parsed_value = json.loads(value)
                if not suppress_log:
                    logger.info("Cache hit ✅", 
                               duration_ms=round((end - start) * 1000, 5), 
                               key=key, 
                               value=parsed_value)
                return parsed_value
            
            logger.info("Cache miss 🙅", key=key)
            return None
            
        except (redis.RedisError, json.JSONDecodeError) as e:
            logger.error("Cache get error ❌", key=key, error=str(e))
            return None
    
    def set(self, key: str, value: Any, expire: Optional[int] = None) -> bool:
        """Set value in cache with optional expiration."""
        if not self.is_connected():
            return False
        
        try:
            if value is not None:
                serialized_value = json.dumps(value)
                
                if expire:
                    result = self.client.setex(key, expire, serialized_value)
                else:
                    result = self.client.set(key, serialized_value)
                
                logger.info("Cache set ✅", key=key, value=value, expire=expire)
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
            logger.info("Cache delete ✅", key=key, deleted=bool(result))
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
    
    def get_info(self) -> dict:
        """Get Redis server information."""
        if not self.is_connected():
            return {}
        
        try:
            return self.client.info()
        except redis.RedisError as e:
            logger.error("Failed to get Redis info", error=str(e))
            return {}
    
    def get_keys(self, pattern: str = "*") -> list:
        """Get keys matching pattern."""
        if not self.is_connected():
            return []
        
        try:
            return self.client.keys(pattern)
        except redis.RedisError as e:
            logger.error("Failed to get keys", pattern=pattern, error=str(e))
            return []
    
    def get_key_count(self) -> int:
        """Get total number of keys in database."""
        if not self.is_connected():
            return 0
        
        try:
            return self.client.dbsize()
        except redis.RedisError as e:
            logger.error("Failed to get key count", error=str(e))
            return 0

# def create_cache() -> RedisCache | NoOpCache:
#     """Create cache instance based on environment variables."""
    
#     # Check if caching is enabled via environment
#     cache_enabled = os.getenv("CACHE_ENABLED", "true").lower() in ("true", "1", "yes", "on")
    
#     if not cache_enabled:
#         logger.info("Caching disabled via CACHE_ENABLED environment variable")
#         return NoOpCache()
    
#     # Get Redis connection parameters from environment
#     host = os.getenv("CACHE_HOST", "localhost")
#     port_str = os.getenv("CACHE_PORT", "6379")
    
#     try:
#         port = int(port_str)
#     except ValueError:
#         logger.warning(f"Invalid CACHE_PORT value: {port_str}, using default 6379")
#         port = 6379
    
#     db_str = os.getenv("CACHE_DB", "0")
#     try:
#         db = int(db_str)
#     except ValueError:
#         logger.warning(f"Invalid CACHE_DB value: {db_str}, using default 0")
#         db = 0
    
#     return RedisCache(host=host, port=port, db=db, enabled=cache_enabled)

# def create_redis_cache(host: str = "localhost", port: int = 6379, db: int = 0) -> RedisCache:
#     """Create a Redis cache instance with specific parameters."""
#     return RedisCache(host=host, port=port, db=db, enabled=True)

# def create_noop_cache() -> NoOpCache:
#     """Create a no-operation cache instance."""
#     return NoOpCache()

# Global cache instance
if os.getenv("CACHE_ENABLED", "False").lower() in ("true", "1", "yes", "on"):
    cache = RedisCache()
else:
    cache = None