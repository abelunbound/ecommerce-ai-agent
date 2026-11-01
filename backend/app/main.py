"""FastAPI application."""

from fastapi import FastAPI

from app.api.router import router

app = FastAPI(title="Lumen & Oak")
app.include_router(router)
