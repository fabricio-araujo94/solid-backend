from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Annotated

from . import crud, models, schemas
from .database import SessionLocal, engine

import random

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

origins = [
    "http://localhost:4200", # Angular
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"], # GET, POST, etc.
    allow_headers=["*"], 
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Endpoints for Part
@app.post("/api/parts/", response_model=schemas.Part, status_code=201)
async def create_new_part(
    db: Session = Depends(get_db),
    name: str = Form(...),
    sku: str = Form(...),
    side_image: UploadFile = File(...),
    frontal_image: UploadFile = File(...)
):
    
    # Check if a part with this SKU already exists
    db_part = crud.get_part_by_sku(db, sku=sku)
    if db_part:
        raise HTTPException(status_code=400, detail=f"SKU '{sku}' already registered.")

    input_side_image_url = f"uploads/images/{side_image.filename}"
    input_front_image_url = f"uploads/images/{front_image.filename}" if secondary_image else None
        
    part_data = schemas.PartCreate(
        name=name,
        sku=sku,
        input_side_image_url=input_side_image_url,
        input_front_image_url=input_front_image_url
    )
    
    return crud.create_part(db=db, part=part_data)

@app.get("/api/parts/", response_model=List[schemas.Part])
def read_all_parts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    parts = crud.get_parts(db, skip=skip, limit=limit)
    return parts

@app.get("/api/parts/{part_id}", response_model=schemas.Part)
def read_one_part(part_id: int, db: Session = Depends(get_db)):
    db_part = crud.get_part(db, part_id=part_id)
    if db_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@app.delete("/api/parts/{part_id}", response_model=schemas.Part)
def delete_existing_part(part_id: int, db: Session = Depends(get_db)):
    deleted_part = crud.delete_part(db, part_id=part_id)
    if deleted_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return deleted_part

@app.get("/api/stats", response_model=schemas.DashboardStats)
def read_dashboard_stats(db: Session = Depends(get_db)):
    stats = crud.get_dashboard_stats(db=db)
    return stats

# Endpoints for ComparisonJob

@app.post("/api/compare/", response_model=schemas.JobResponse)
async def create_comparison_job(
    db: Session = Depends(get_db),
    part_id: int = Form(...),
    imagem_frontal: UploadFile = File(...),
    imagem_lateral: UploadFile = File(...)
):
    job_id = "simulated-job-12345" # This would be the real ID from the DB
    print(f"Job created with ID: {job_id} for part {part_id}")
    
    return {"jobId": job_id}


@app.get("/api/compare/status/{job_id}", response_model=schemas.JobStatusResponse)
def get_job_status(job_id: str, db: Session = Depends(get_db)):
    print(f"Checking status for job: {job_id}")
    
    if random.random() < 0.7: # 70% chance of still processing
        return {"status": "processing"}
    else:
        return {
            "status": "complete",
            "modelUrl": "uploads/models/result-model.gltf"
        }