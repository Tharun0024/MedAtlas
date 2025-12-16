# backend/api_main.py  (put it directly under backend/, not inside api/ if you prefer)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.endpoints.providers import router as providers_router
from backend.api.endpoints.export import router as export_router
from backend.api.endpoints.discrepancies import router as discrepancies_router
from backend.api.endpoints.validate import router as validate_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(providers_router)
app.include_router(export_router)
app.include_router(discrepancies_router)
app.include_router(validate_router)
