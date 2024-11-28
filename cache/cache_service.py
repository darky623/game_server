import json
from functools import wraps
from fastapi import Request
import hashlib

from pydantic import BaseModel

from cache.config import RedisConfig
from redis.asyncio import Redis


class CacheService:
    def __init__(self, redis_config: RedisConfig):
        self.redis_config = redis_config
        self.redis = Redis(**self.redis_config.__dict__)

    async def __get_cache(self, key: str):
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def __set_cache(self, key: str, value: dict | BaseModel | list, ttl: int):
        await self.redis.setex(key, ttl, json.dumps(value))

    def cache_response(self, ttl: int):
        def decorator(func):
            @wraps(func)
            async def wrapper(*args, **kwargs):
                request: Request = kwargs.get('request')
                if request:
                    key = f"{request.url.path}?{request.query_params}"
                else:
                    key = func.__name__

                cache_key = hashlib.sha256(key.encode()).hexdigest()

                # Проверяем кеш
                cached_response = await self.__get_cache(cache_key)
                if cached_response:
                    return cached_response

                # Получаем новый ответ
                response = await func(*args, **kwargs)

                # Кешируем ответ
                if response:
                    if isinstance(response, BaseModel):
                        await self.__set_cache(cache_key, response.model_dump(), ttl)
                    elif isinstance(response, list) and response and isinstance(response[0], BaseModel):
                        await self.__set_cache(cache_key, [schema.model_dump() for schema in response], ttl)

                return response

            return wrapper
        return decorator
