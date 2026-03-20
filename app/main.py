from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.dependencies.db import get_db
from app.db.indexes import create_indexes


@asynccontextmanager
async def lifespan(app: FastAPI):
    db = await get_db()
    await create_indexes(db)
    yield


app = FastAPI(
    title="Medication Reconciliation Service",
    version="1.0.0",
    lifespan=lifespan
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # better than "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def health():
    return {"status": "ok"}