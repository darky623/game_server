from cache.config import RedisConfig
from cache.cache_service import CacheService

cache_service = CacheService(RedisConfig())