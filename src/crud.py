from sqlalchemy.orm import Session
from typing import Optional
from . import models, schemas

# CRUD functions for Part
def get_part(db: Session, part_id: int):
    """Fetches a single part by its primary key ID."""
    return db.query(models.Part).filter(models.Part.id == part_id).first()

def get_part_by_sku(db: Session, sku: str):
    """Fetches a single part by its unique SKU."""
    return db.query(models.Part).filter(models.Part.sku == sku).first()

def get_parts(db: Session, skip: int = 0, limit: int = 100):
    """Fetches a list of parts with pagination."""
    return db.query(models.Part).offset(skip).limit(limit).all()

def create_part(db: Session, part: schemas.PartCreate):
    """Creates a new standard part in the database."""
    # The schema is converted to a dictionary and then passed to the SQLAlchemy model
    db_part = models.Part(**part.model_dump())
    db.add(db_part)
    db.commit()
    db.refresh(db_part)
    return db_part

def delete_part(db: Session, part_id: int):
    """Deletes a part from the database by its ID."""
    db_part = get_part(db, part_id=part_id)
    if db_part:
        db.delete(db_part)
        db.commit()
        return db_part
    return None

# CRUD functions for ComparisonJob
def get_job(db: Session, job_id: int):
    """Fetches a single comparison job by its ID."""
    return db.query(models.ComparisonJob).filter(models.ComparisonJob.id == job_id).first()

def create_job(db: Session, job: schemas.ComparisonJobCreate):
    """Creates a new comparison job in the database."""
    db_job = models.ComparisonJob(**job.model_dump())
    db.add(db_job)
    db.commit()
    db.refresh(db_job)
    return db_job

def update_job_status(db: Session, job_id: int, status: str, output_url: Optional[str] = None):
    """Updates the status and optionally the output URL of a job."""
    db_job = get_job(db, job_id=job_id)
    if db_job:
        db_job.status = status
        if output_url:
            db_job.output_model_url = output_url
        
        db.commit()
        db.refresh(db_job)
        return db_job
    return None
    
    
def get_dashboard_stats(db: Session):
    """
    Calculates and returns the main dashboard statistics.
    """
    total_parts = db.query(models.Part).count()
    
    total_analyses = db.query(models.ComparisonJob).count()
    
    # Assuming 'active' jobs are those with 'PENDING' or 'PROCESSING' status
    active_comparisons = db.query(models.ComparisonJob).filter(
        models.ComparisonJob.status.in_(['PENDING', 'PROCESSING'])
    ).count()

    return {
        "totalParts": total_parts,
        "totalAnalyses": total_analyses,
        "activeComparisons": active_comparisons,
    }
