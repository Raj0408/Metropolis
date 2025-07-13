import redis
from .settings import settings


redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=int(settings.REDIS_PORT),
    db=0,
    decode_responses=True
)

READY_QUEUE_NAME = "metropolis:ready_queue"