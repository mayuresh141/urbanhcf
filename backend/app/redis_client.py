import os
import redis
import logging

logger = logging.getLogger("redis_client")

_redis_client = None

def get_redis_client(redis_url: str):
    global _redis_client

    if _redis_client is None:
        if not redis_url:
            raise RuntimeError("Redis URL was not provided")

        logger.info(f"Using Redis URL: {redis_url}")

        _redis_client = redis.StrictRedis.from_url(
            redis_url,
            decode_responses=True
        )

    return _redis_client
