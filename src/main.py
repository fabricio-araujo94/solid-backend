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
origins = ["http://localhost:4200"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"], 
)

# Include Routers
app.include_router(parts.router)
app.include_router(comparison.router)
app.include_router(analysis.router)
app.include_router(stats.router)