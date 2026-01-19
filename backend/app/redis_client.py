import os
import redis
from urllib.parse import urlparse
import logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("redis_client")
# Get Redis connection URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")  # fallback for local

logger.info(f"Using Redis URL: {REDIS_URL}")

redis_client = redis.StrictRedis.from_url(
    REDIS_URL,
    decode_responses=True
)
