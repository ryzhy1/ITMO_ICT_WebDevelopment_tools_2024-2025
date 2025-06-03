from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from celery.result import AsyncResult
import celery
from celery_app import parse_urls_task
from main import AsyncioParser

app = FastAPI(title="OKVED Parser API")
celery_app = celery.Celery(broker="redis://redis:6379/0", backend="redis://redis:6379/1")

class URLList(BaseModel):
    urls: List[str]

@app.post("/parse")
async def parse_okved(payload: URLList):
    if not payload.urls:
        raise HTTPException(400, "Список URL-ов пуст")

    parser = AsyncioParser(payload.urls)

    d = await parser.run()

    return {"elapsed_sec": d, "saved": len(payload.urls)}

@app.post("/parse_async")
def enqueue_parse(req: URLList):
    if not req.urls:
        raise HTTPException(400, "Список URL-ов пуст")
    job = parse_urls_task.delay(req.urls)
    return {"task_id": job.id, "status": "queued"}

@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    res: AsyncResult = celery_app.AsyncResult(task_id)
    if res.state == "PENDING":
        return {"status": "pending"}
    if res.state == "SUCCESS":
        return {"status": "done", "result": res.result}
    if res.state == "FAILURE":
        return {"status": "failed", "error": str(res.result)}
    return {"status": res.state.lower()}
