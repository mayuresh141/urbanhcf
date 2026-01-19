import os
import redis
from urllib.parse import urlparse

# Get Redis connection URL
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379")  # fallback for local

# Parse the URL
parsed = urlparse(REDIS_URL)

redis_client = redis.Redis(
    host=parsed.hostname,
    port=parsed.port,
    password=parsed.password,  # None if not provided
    decode_responses=True,      # allows storing JSON/strings
    ssl=True if parsed.hostname != "localhost" else False  # SSL required for Render KV
)
