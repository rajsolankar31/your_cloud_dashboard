from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api.routes import router
from .database.db import init_db
from .security import secrets
from .services.sync import sync_all


@asynccontextmanager
async def lifespan(app: FastAPI):
    secrets.load()
    init_db()
    sync_all()  # first load; later syncs are manual
    yield


app = FastAPI(title="Unified Cloud Dashboard", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
                   allow_methods=["*"], allow_headers=["*"])
app.include_router(router)
