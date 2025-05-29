from fastapi import FastAPI
from sqlmodel import create_engine, SQLModel
from src.finance.routes import router as finance_router
from src.auth.routes import router as auth_router
from dotenv import load_dotenv
import os
import logging

load_dotenv()

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Finance API",
    description="API для управления личными финансами",
    version="1.0.0",
)

# Создаём таблицы в базе данных
engine = create_engine(os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres"))
SQLModel.metadata.create_all(engine)

app.include_router(finance_router, prefix="/finance", tags=["finance"])
app.include_router(auth_router, prefix="/auth", tags=["auth"])