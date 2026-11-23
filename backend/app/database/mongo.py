from functools import lru_cache

from pymongo import AsyncMongoClient
from pymongo.asynchronous.database import AsyncDatabase

from ..config.settings import get_settings


@lru_cache(maxsize=1)
def get_mongo_client() -> AsyncMongoClient:
    settings = get_settings()
    return AsyncMongoClient(settings.mongo_uri, maxPoolSize=20, minPoolSize=1, tz_aware=True)


def get_database() -> AsyncDatabase:
    return get_mongo_client()[get_settings().mongo_database]