from celery import Celery
from main import AsyncioParser

REDIS_BROKER = "redis://redis:6379/0"
REDIS_BACKEND = "redis://redis:6379/1"

celery_app = Celery(
    "okved_tasks",
    broker=REDIS_BROKER,
    backend=REDIS_BACKEND,
)

@celery_app.task(name="okved.parse_urls")
def parse_urls_task(urls: list[str]) -> dict:
    elapsed = AsyncioParser(urls).run()
    return {"elapsed_sec": elapsed, "saved": len(urls)}