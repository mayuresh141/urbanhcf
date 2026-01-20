import os
import redis
import logging

logger = logging.getLogger("redis_client")

_redis_client = None

def get_redis_client():
    global _redis_client

    if _redis_client is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        print("inside if loop", redis_url)
        logger.info(f"Using Redis URL: {redis_url}")

        _redis_client = redis.StrictRedis.from_url(
            redis_url,
            decode_responses=True
        )

    return _redis_client
