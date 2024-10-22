from dataclasses import dataclass
from os import getenv


@dataclass
class RedisConfig:
    host: str = 'localhost'
    port: int = '6379'
    # db: int = getenv("REDIS_DB")
    # password: str = getenv("REDIS_PASSWORD")


