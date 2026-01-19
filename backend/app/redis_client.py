import os
import redis
from urllib.parse import urlparse

# Get Redis connection URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")  # fallback for local

# Parse the URL
parsed = urlparse(REDIS_URL)

redis_client = redis.StrictRedis.from_url(
    REDIS_URL,
    decode_responses=False
)
