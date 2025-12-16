from sqlalchemy.orm import Session
from typing import List, Optional
from ..domain import models, schemas
from .interfaces import IPartRepository, IJobRepository, IStatsRepository

class SqlAlchemyPartRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_part(self, part_id: int) -> Optional[models.Part]:
        return self.db.query(models.Part).filter(models.Part.id == part_id).first()

    def get_part_by_sku(self, sku: str) -> Optional[models.Part]:
        return self.db.query(models.Part).filter(models.Part.sku == sku).first()

    def get_parts(self, skip: int = 0, limit: int = 100, part_type: Optional[str] = None) -> List[models.Part]:
        query = self.db.query(models.Part)
        if part_type:
            query = query.filter(models.Part.part_type == part_type)
        return query.offset(skip).limit(limit).all()

    def create_part(self, part: schemas.PartCreate) -> models.Part:
        db_part = models.Part(**part.model_dump())
        self.db.add(db_part)
        self.db.commit()
        self.db.refresh(db_part)
        return db_part

    def delete_part(self, part_id: int) -> Optional[models.Part]:
        db_part = self.get_part(part_id)
        if db_part:
            self.db.delete(db_part)
            self.db.commit()
            return db_part
        return None

class SqlAlchemyJobRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_job(self, job_id: int) -> Optional[models.ComparisonJob]:
        return self.db.query(models.ComparisonJob).filter(models.ComparisonJob.id == job_id).first()

    def create_job(self, job: schemas.ComparisonJobCreate) -> models.ComparisonJob:
        db_job = models.ComparisonJob(**job.model_dump())
        self.db.add(db_job)
        self.db.commit()
        self.db.refresh(db_job)
        return db_job

    def update_job_status(self, job_id: int, status: str, output_url: Optional[str] = None) -> Optional[models.ComparisonJob]:
        db_job = self.get_job(job_id)
        if db_job:
            db_job.status = status
            if output_url:
                db_job.output_model_url = output_url
            self.db.commit()
            self.db.refresh(db_job)
            return db_job
        return None

    def get_jobs_by_part(self, part_id: int) -> List[models.ComparisonJob]:
        return self.db.query(models.ComparisonJob).filter(models.ComparisonJob.part_id == part_id).all()

class SqlAlchemyStatsRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_dashboard_stats(self) -> dict:
        total_parts = self.db.query(models.Part).count()
        total_analyses = self.db.query(models.ComparisonJob).count()
        
        # Assuming 'active' jobs are those with 'PENDING' or 'PROCESSING' status
        active_comparisons = self.db.query(models.ComparisonJob).filter(
            models.ComparisonJob.status.in_(['PENDING', 'PROCESSING'])
        ).count()

        return {
            "totalParts": total_parts,
            "totalAnalyses": total_analyses,
            "activeComparisons": active_comparisons,
        }
