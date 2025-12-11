from fastapi import Depends
from sqlalchemy.orm import Session
from .database import get_db
from ..repositories.interfaces import IPartRepository, IJobRepository, IStatsRepository
from ..repositories.sqlalchemy_impl import SqlAlchemyPartRepository, SqlAlchemyJobRepository, SqlAlchemyStatsRepository
from ..services.storage import IFileStorage, LocalFileStorage, CloudinaryFileStorage
from ..services.defect_service import DefectService, OpenCVContrastDefectDetector
import os

def get_part_repository(db: Session = Depends(get_db)) -> IPartRepository:
    return SqlAlchemyPartRepository(db)

def get_job_repository(db: Session = Depends(get_db)) -> IJobRepository:
    return SqlAlchemyJobRepository(db)

def get_stats_repository(db: Session = Depends(get_db)) -> IStatsRepository:
    return SqlAlchemyStatsRepository(db)

def get_file_storage() -> IFileStorage:
    if os.getenv("CLOUDINARY_URL"):
        return CloudinaryFileStorage()
    return LocalFileStorage(base_url=os.getenv("API_BASE_URL", "http://localhost:8000"))

def get_defect_service() -> DefectService:
    # Injecting the concrete strategy here (Composition Root for this scope)
    return DefectService(OpenCVContrastDefectDetector())
