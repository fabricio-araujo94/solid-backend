from sqlalchemy.orm import Session
from ..services import reconstruction_service
from ..services.reconstruction_service import ReconstructionService, SilhouetteReconstructionStrategy
from ..core.database import SessionLocal
from ..repositories.sqlalchemy_impl import SqlAlchemyPartRepository, SqlAlchemyJobRepository
import os

def process_part_3d_generation(part_id: int, front_bytes: bytes, side_bytes: bytes):
    """Generates the 3D model for the Standard Part (Reference) in a worker process."""
    db = SessionLocal()
    part_repo = SqlAlchemyPartRepository(db)
    
    # Composition Root for Worker Scope
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    try:
        # Call service with 'part' prefix
        model_path = service.process(
            front_bytes, side_bytes, "part", part_id
        )
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        web_url = f"{base_url}/{model_path.replace(os.sep, '/')}"
        
        # Updates the part's model_3d_url field
        part = part_repo.get_part(part_id)
        if part:
            part.model_3d_url = web_url
            db.commit()
            print(f"Part {part_id} updated with 3D model: {web_url}")
    except Exception as e:
        print(f"Critical Error generating 3D for part {part_id}: {e}")
    finally:
        db.close()

def process_job_3d_generation(job_id: int, front_bytes: bytes, side_bytes: bytes):
    """Generates the 3D model for the Comparison Job in a worker process."""
    db = SessionLocal()
    job_repo = SqlAlchemyJobRepository(db)
    
    # Composition Root for Worker Scope
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    try:
        # Updates status to PROCESSING
        job_repo.update_job_status(job_id, "PROCESSING")
        
        # Call service with 'job' prefix
        model_path = service.process(
            front_bytes, side_bytes, "job", job_id
        )
        base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
        web_url = f"{base_url}/{model_path.replace(os.sep, '/')}"
        
        # Success
        job_repo.update_job_status(job_id, "COMPLETE", output_url=web_url)
        print(f"Job {job_id} completed: {web_url}")
        
    except Exception as e:
        print(f"Critical Error in Job {job_id}: {e}")
        job_repo.update_job_status(job_id, "FAILED")
    finally:
        db.close()
