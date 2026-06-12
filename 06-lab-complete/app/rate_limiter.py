import redis
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL)

def check_rate_limit(user_id: str):
    key = f"rate_limit:{user_id}"
    current = r.get(key)
    if current and int(current) >= settings.RATE_LIMIT_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Rate limit exceeded")
    
    pipe = r.pipeline()
    pipe.incr(key)
    pipe.expire(key, 60)
    pipe.execute()
