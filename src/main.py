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
    front_image: UploadFile = File(...)
):
    
    # Check if a part with this SKU already exists
    db_part = crud.get_part_by_sku(db, sku=sku)
    if db_part:
        raise HTTPException(status_code=400, detail=f"SKU '{sku}' already registered.")

    side_image_url = f"uploads/images/{side_image.filename}"
    front_image_url = f"uploads/images/{front_image.filename}" 
        
    part_data = schemas.PartCreate(
        name=name,
        sku=sku,
        side_image_url=side_image_url,
        front_image_url=front_image_url
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

@app.get("/api/parts/{part_id}/jobs", response_model=List[schemas.ComparisonJob])
def read_jobs_by_part(part_id: int, db: Session = Depends(get_db)):
    """
    Returns the history of comparisons (inspections) for a specific part.
    """
    
    db_part = crud.get_part(db, part_id=part_id)
    if db_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    
    # Since the relationship is configured in models.py, we can access it directly
    # or make a query filtering by ID. The query is safer if the list is large.
    jobs = db.query(models.ComparisonJob).filter(models.ComparisonJob.part_id == part_id).all()
    return jobs

# Endpoints for ComparisonJob

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

@app.post("/api/compare/", response_model=schemas.ComparisonJob)
async def create_and_run_comparison(
    db: Session = Depends(get_db),
    part_id: int = Form(...),
    input_side_image: UploadFile = File(...),
    input_front_image: UploadFile = File(...)
):
    """
    Receives images, saves the record, and immediately returns
    the result with a placeholder 3D model URL.
    """
    
    front_image_url = f"uploads/inputs/{input_side_image.filename}"
    side_image_url = f"uploads/inputs/{input_front_image.filename}"
    # TODO: Implementar o salvamento real dos arquivos.

    placeholder_model_url = "src\examples\key.stl"

    job_schema = schemas.ComparisonJobCreate(
        part_id=part_id,
        input_front_image_url=front_image_url,
        input_side_image_url=side_image_url
    )
    db_job = crud.create_job(db=db, job=job_schema)

    return crud.update_job_status(
        db=db, 
        job_id=db_job.id, 
        status="COMPLETE", 
        output_url=placeholder_model_url
    )