from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
import signal
import sys
import logging
import json
import redis
from contextlib import asynccontextmanager

from .config import settings
from .auth import verify_api_key
from .rate_limiter import check_rate_limit
from .cost_guard import check_budget

# Setup JSON logging
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
        }
        return json.dumps(log_record)

logger = logging.getLogger("agent")
logger.setLevel(settings.LOG_LEVEL)
handler = logging.StreamHandler()
handler.setFormatter(JSONFormatter())
logger.addHandler(handler)

r = redis.from_url(settings.REDIS_URL)
is_shutting_down = False

def graceful_shutdown(signum, frame):
    global is_shutting_down
    logger.info("Received shutdown signal. Commencing graceful shutdown...")
    is_shutting_down = True

signal.signal(signal.SIGTERM, graceful_shutdown)
signal.signal(signal.SIGINT, graceful_shutdown)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application starting up...")
    yield
    logger.info("Application shutting down...")

app = FastAPI(lifespan=lifespan)

# Phục vụ file tĩnh (Frontend)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def serve_frontend():
    return FileResponse("frontend/index.html")

class AskRequest(BaseModel):
    user_id: str
    question: str

@app.get("/health")
def health():
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Shutting down")
    return {"status": "ok"}

@app.get("/ready")
def ready():
    if is_shutting_down:
        raise HTTPException(status_code=503, detail="Shutting down")
    try:
        r.ping()
        return {"status": "ready"}
    except Exception as e:
        logger.error(f"Readiness check failed: {str(e)}")
        raise HTTPException(status_code=503, detail="Not ready")

@app.post("/ask", dependencies=[Depends(verify_api_key)])
def ask(request: AskRequest):
    user_id = request.user_id
    question = request.question
    
    # Rate limit and Cost guard
    check_rate_limit(user_id)
    check_budget(user_id, estimated_cost=0.01)
    
    # Stateless logic: Retrieve history from Redis
    history_key = f"history:{user_id}"
    history = r.lrange(history_key, 0, -1)
    history = [msg.decode('utf-8') for msg in history]
    
    # Mock LLM Agent
    history_text = " | ".join(history)
    if history and any(word in question.lower() for word in ["name", "who am i", "remember"]):
        response_text = f"You mentioned previously: {history_text}. I remember you!"
    else:
        response_text = f"Mock response to: {question}"
    
    # Save to Redis
    r.rpush(history_key, question)
    r.rpush(history_key, response_text)
    r.expire(history_key, 3600) # expire in 1 hour
    
    logger.info(f"Processed question from {user_id}")
    
    return {"response": response_text}
