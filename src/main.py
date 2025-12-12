from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os

from .domain import models
from .core.database import engine
from .routers import parts, comparison, analysis, stats

# Create tables if they don't exist
models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Static Folders Configuration
os.makedirs("static/images", exist_ok=True)
os.makedirs("uploads/inputs", exist_ok=True)
os.makedirs("uploads/models", exist_ok=True)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# CORS Configuration
allowed_origins_env = os.getenv("ALLOWED_ORIGINS")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://urban-enigma-gwvgrg94j4x3wq7g-4200.app.github.dev",
        "https://special-rotary-phone-pvwjvqvv95c99jp-8000.app.github.dev"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Include Routers
app.include_router(parts.router)
app.include_router(comparison.router)
app.include_router(analysis.router)
app.include_router(stats.router)