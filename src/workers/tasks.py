from sqlalchemy.orm import Session
from ..services import reconstruction_service
from ..services.reconstruction_service import ReconstructionService, SilhouetteReconstructionStrategy
from ..core.database import SessionLocal
from ..repositories.sqlalchemy_impl import SqlAlchemyPartRepository, SqlAlchemyJobRepository
import os

def process_part_3d_generation(part_id: int, front_url: str, side_url: str):
    """Generates the 3D model for the Standard Part (Reference) in a worker process."""
    
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    # Models will be kept locally in uploads/models (no cloud upload)

    import requests
    import tempfile
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_front, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_side:
            
            tf_front.write(requests.get(front_url).content)
            tf_side.write(requests.get(side_url).content)
            
            front_path = tf_front.name
            side_path = tf_side.name

        try:
            # Call service with file paths (service already saves model to uploads/models)
            local_model_path = service.process(
                front_path, side_path, "part", part_id
            )

            # Build a local URL to the saved model instead of uploading to Cloudinary
            base_url = os.getenv("API_BASE_URL", "https://special-rotary-phone-pvwjvqvv95c99jp-8000.app.github.dev")
            web_url = f"{base_url}/uploads/models/{os.path.basename(local_model_path)}"

            # Updates the part's model_3d_url field with the local URL
            # OPEN DB SESSION ONLY HERE
            db = SessionLocal()
            try:
                part_repo = SqlAlchemyPartRepository(db)
                part = part_repo.get_part(part_id)
                if part:
                    part.model_3d_url = web_url
                    db.commit()
                    print(f"Part {part_id} updated with 3D model: {web_url}")
            finally:
                db.close()

        finally:
            if os.path.exists(front_path): os.remove(front_path)
            if os.path.exists(side_path): os.remove(side_path)

    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Critical Error generating 3D for part {part_id}: {e}")

def process_job_3d_generation(job_id: int, front_url: str, side_url: str):
    """Generates the 3D model for the Comparison Job in a worker process."""
    
    db = SessionLocal()
    try:
        job_repo = SqlAlchemyJobRepository(db)
        job_repo.update_job_status(job_id, "PROCESSING")
    finally:
        db.close()
    
    # Composition Root for Worker Scope
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    # Models will be kept locally in uploads/models (no cloud upload)

    import requests
    import tempfile
    
    try:
        # Download images to temp files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_front, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_side:
            
            tf_front.write(requests.get(front_url).content)
            tf_side.write(requests.get(side_url).content)
            
            front_path = tf_front.name
            side_path = tf_side.name

            try:
                # Call service with 'job' prefix (service already saves model to uploads/models)
                local_model_path = service.process(
                    front_path, side_path, "job", job_id
                )

                # Build a local URL to the saved model instead of uploading to Cloudinary
                base_url = os.getenv("API_BASE_URL", "https://special-rotary-phone-pvwjvqvv95c99jp-8000.app.github.dev")
                web_url = f"{base_url}/uploads/models/{os.path.basename(local_model_path)}"

                # 2. Update status to COMPLETE (Quick DB access)
                db = SessionLocal()
                try:
                    job_repo = SqlAlchemyJobRepository(db)
                    job_repo.update_job_status(job_id, "COMPLETE", output_url=web_url)
                    print(f"Job {job_id} completed: {web_url}")
                finally:
                    db.close()
                
            finally:
                if os.path.exists(front_path): os.remove(front_path)
                if os.path.exists(side_path): os.remove(side_path)
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Critical Error in Job {job_id}: {e}")
        
        # 3. Update status to FAILED (Quick DB access)
        db = SessionLocal()
        try:
            job_repo = SqlAlchemyJobRepository(db)
            job_repo.update_job_status(job_id, "FAILED")
        finally:
             db.close()
