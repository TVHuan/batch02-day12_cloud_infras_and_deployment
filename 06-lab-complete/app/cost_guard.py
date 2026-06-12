import redis
from datetime import datetime
from fastapi import HTTPException
from .config import settings

r = redis.from_url(settings.REDIS_URL)

def check_budget(user_id: str, estimated_cost: float = 0.01):
    month_key = datetime.now().strftime("%Y-%m")
    key = f"budget:{user_id}:{month_key}"
    
    current = float(r.get(key) or 0)
    if current + estimated_cost > settings.MONTHLY_BUDGET_USD:
        raise HTTPException(status_code=402, detail="Budget exceeded")
    
    pipe = r.pipeline()
    pipe.incrbyfloat(key, estimated_cost)
    pipe.expire(key, 32 * 24 * 3600)
    pipe.execute()
