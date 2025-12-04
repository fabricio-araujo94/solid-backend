from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Annotated

import uuid
import os
import shutil
import random

from . import crud, models, schemas, defect_service, reconstruction_service
from .database import SessionLocal, engine

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- WORKERS (Background Tasks) ---

def process_part_3d_generation(part_id: int, front_bytes: bytes, side_bytes: bytes, db: Session):
    """Generates the 3D model for the Standard Part (Reference)"""
    try:
        # Call service with 'part' prefix
        model_path = reconstruction_service.process_images_to_3d(
            front_bytes, side_bytes, "part", part_id
        )
        web_url = f"http://localhost:8000/{model_path.replace(os.sep, '/')}"
        
        # Updates the part's model_3d_url field
        part = crud.get_part(db, part_id)
        if part:
            part.model_3d_url = web_url
            db.commit()
            print(f"Part {part_id} updated with 3D model: {web_url}")
    except Exception as e:
        print(f"Critical Error generating 3D for part {part_id}: {e}")

def process_job_3d_generation(job_id: int, front_bytes: bytes, side_bytes: bytes, db: Session):
    """Generates the 3D model for the Comparison Job"""
    try:
        # Updates status to PROCESSING
        crud.update_job_status(db, job_id, "PROCESSING")
        
        # Call service with 'job' prefix
        model_path = reconstruction_service.process_images_to_3d(
            front_bytes, side_bytes, "job", job_id
        )
        web_url = f"http://localhost:8000/{model_path.replace(os.sep, '/')}"
        
        # Success
        crud.update_job_status(db, job_id, "COMPLETE", output_url=web_url)
        print(f"Job {job_id} completed: {web_url}")
        
    except Exception as e:
        print(f"Critical Error in Job {job_id}: {e}")
        crud.update_job_status(db, job_id, "FAILED")

# --- ENDPOINTS ---

@app.post("/api/parts/", response_model=schemas.Part, status_code=201)
async def create_new_part(
    background_tasks: BackgroundTasks, # Injection for background tasks
    db: Session = Depends(get_db),
    name: str = Form(...),
    sku: str = Form(...),
    side_image: UploadFile = File(...),   # name="side_image" in Angular
    front_image: UploadFile = File(...)   # name="front_image" in Angular
):
    # 1. Verify SKU
    db_part = crud.get_part_by_sku(db, sku=sku)
    if db_part:
        raise HTTPException(status_code=400, detail=f"SKU '{sku}' already registered.")

    # 2. Read bytes to use in 3D generation
    front_bytes = await front_image.read()
    side_bytes = await side_image.read()
    
    # 3. Save static images for display (2D Reference)
    STATIC_IMAGES_DIR = "static/images"
    
    def save_bytes_to_disk(file_bytes, original_filename):
        file_extension = original_filename.split('.')[-1]
        unique_filename = f"{uuid.uuid4()}.{file_extension}"
        file_path = os.path.join(STATIC_IMAGES_DIR, unique_filename)
        with open(file_path, "wb") as f:
            f.write(file_bytes)
        return f"http://localhost:8000/static/images/{unique_filename}"

    side_url = save_bytes_to_disk(side_bytes, side_image.filename)
    front_url = save_bytes_to_disk(front_bytes, front_image.filename)

    # 4. Create record in Database
    part_data = schemas.PartCreate(
        name=name,
        sku=sku,
        side_image_url=side_url,
        front_image_url=front_url
    )
    new_part = crud.create_part(db=db, part=part_data)

    # 5. Trigger 3D Generation in Background (To create the reference model)
    background_tasks.add_task(
        process_part_3d_generation,
        new_part.id,
        front_bytes,
        side_bytes,
        db
    )
    
    return new_part

@app.get("/api/parts/", response_model=List[schemas.Part])
def read_all_parts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_parts(db, skip=skip, limit=limit)

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

@app.get("/api/parts/{part_id}/jobs", response_model=List[schemas.ComparisonJob])
def read_jobs_by_part(part_id: int, db: Session = Depends(get_db)):
    db_part = crud.get_part(db, part_id=part_id)
    if db_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    jobs = db.query(models.ComparisonJob).filter(models.ComparisonJob.part_id == part_id).all()
    return jobs

# --- COMPARISON ENDPOINTS (Jobs) ---

@app.post("/api/compare/", response_model=schemas.ComparisonJob)
async def create_and_run_comparison(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    # UPDATED: Parameters now match the English names sent by Angular
    reference_part_id: int = Form(...), 
    front_image: UploadFile = File(...), 
    side_image: UploadFile = File(...)  
):
    # 1. Read bytes
    front_bytes = await front_image.read()
    side_bytes = await side_image.read()
    
    # 2. Save inputs (optional, good for logging)
    input_dir = "uploads/inputs"
    front_filename = f"job_{uuid.uuid4()}_{front_image.filename}"
    side_filename = f"job_{uuid.uuid4()}_{side_image.filename}"
    
    front_path = os.path.join(input_dir, front_filename)
    side_path = os.path.join(input_dir, side_filename)
    
    with open(front_path, "wb") as f: f.write(front_bytes)
    with open(side_path, "wb") as f: f.write(side_bytes)

    # 3. Create Job PENDING
    job_schema = schemas.ComparisonJobCreate(
        part_id=reference_part_id,
        input_front_image_url=f"http://localhost:8000/{front_path.replace(os.sep, '/')}",
        input_side_image_url=f"http://localhost:8000/{side_path.replace(os.sep, '/')}"
    )
    db_job = crud.create_job(db=db, job=job_schema)

    # 4. Trigger Heavy Task
    background_tasks.add_task(
        process_job_3d_generation, 
        db_job.id, 
        front_bytes, 
        side_bytes, 
        db
    )

    return db_job

@app.get("/api/compare/status/{job_id}", response_model=schemas.JobStatusResponse)
def get_job_status(job_id: int, db: Session = Depends(get_db)):
    # Now we fetch the REAL status from the database
    job = db.query(models.ComparisonJob).filter(models.ComparisonJob.id == job_id).first()
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    # Map to response schema
    return {
        "status": job.status.lower(), # 'pending', 'processing', 'complete', 'failed'
        "modelUrl": job.output_model_url
    }

@app.put("/api/compare/{job_id}/status", response_model=schemas.ComparisonJob)
def update_job_status_final(job_id: int, new_status: str = None, db: Session = Depends(get_db)):
    """
    Updates the status of a comparison job to APPROVED or REJECTED.
    Expected call: PUT /api/compare/123/status?new_status=APPROVED
    """
    db_job = db.query(models.ComparisonJob).filter(models.ComparisonJob.id == job_id).first()
    if db_job is None:
        raise HTTPException(status_code=404, detail="Comparison Job not found")
    
    if not new_status or new_status.upper() not in ["APPROVED", "REJECTED"]:
        raise HTTPException(status_code=400, detail="Invalid status. Must be APPROVED or REJECTED. Use: ?new_status=APPROVED")

    db_job.status = new_status.upper()
    db.commit()
    db.refresh(db_job)
    return db_job

# --- AI ENDPOINT (Defect Detection) ---

@app.post("/api/analyze/defects", response_model=schemas.DefectAnalysisResponse)
async def analyze_defects(file: UploadFile = File(...)):
    contents = await file.read()
    try:
        result = defect_service.analyze_image_for_defects(contents)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.get("/api/stats", response_model=schemas.DashboardStats)
def read_dashboard_stats(db: Session = Depends(get_db)):
    return crud.get_dashboard_stats(db=db)