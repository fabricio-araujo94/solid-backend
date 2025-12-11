from sqlalchemy.orm import Session
from ..services import reconstruction_service
from ..services.reconstruction_service import ReconstructionService, SilhouetteReconstructionStrategy
from ..core.database import SessionLocal
from ..repositories.sqlalchemy_impl import SqlAlchemyPartRepository, SqlAlchemyJobRepository
import os

def process_part_3d_generation(part_id: int, front_url: str, side_url: str):
    """Generates the 3D model for the Standard Part (Reference) in a worker process."""
    db = SessionLocal()
    part_repo = SqlAlchemyPartRepository(db)
    
    # Composition Root for Worker Scope
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    # Needs storage to upload the result
    from ..core.dependencies import get_file_storage
    file_storage = get_file_storage()

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
            # Call service with file paths
            # The service returns a physical path (likely in 'uploads/models' or temp)
            # But the service (SilhouetteReconstructionStrategy) currently saves to OUTPUT_DIR = "uploads/models"
            # We should probably let it save there (ephemeral) and then we upload it.
            
            local_model_path = service.process(
                front_path, side_path, "part", part_id
            )
            
            # Upload the generated model to Storage (Cloudinary)
            with open(local_model_path, "rb") as model_file:
                # Use stream to upload to avoid reading full STL into RAM if possible, though STL isn't huge.
                _, web_url = file_storage.save_stream(model_file, os.path.basename(local_model_path), "uploads/models")
            
            # Updates the part's model_3d_url field with the Cloudinary URL
            part = part_repo.get_part(part_id)
            if part:
                part.model_3d_url = web_url
                db.commit()
                print(f"Part {part_id} updated with 3D model: {web_url}")
                
        finally:
            # Cleanup temp input files
            if os.path.exists(front_path): os.remove(front_path)
            if os.path.exists(side_path): os.remove(side_path)
            # Cleanup generated model file (if it was local)
            # local_model_path is likely inside 'uploads/models'. 
            # We can leave it or remove it. Render is ephemeral so it doesn't matter much.
            if os.path.exists(local_model_path): os.remove(local_model_path)

    except Exception as e:
        print(f"Critical Error generating 3D for part {part_id}: {e}")
    finally:
        db.close()

def process_job_3d_generation(job_id: int, front_url: str, side_url: str):
    """Generates the 3D model for the Comparison Job in a worker process."""
    db = SessionLocal()
    job_repo = SqlAlchemyJobRepository(db)
    
    # Composition Root for Worker Scope
    strategy = SilhouetteReconstructionStrategy()
    service = ReconstructionService(strategy)
    
    # Needs storage to upload the result
    from ..core.dependencies import get_file_storage
    file_storage = get_file_storage()

    import requests
    import tempfile
    
    try:
        # Updates status to PROCESSING
        job_repo.update_job_status(job_id, "PROCESSING")
        
        # Download images to temp files
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_front, \
             tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tf_side:
            
            tf_front.write(requests.get(front_url).content)
            tf_side.write(requests.get(side_url).content)
            
            front_path = tf_front.name
            side_path = tf_side.name

        try:
            # Call service with 'job' prefix
            local_model_path = service.process(
                front_path, side_path, "job", job_id
            )
            
            # Upload the generated model to Storage
            with open(local_model_path, "rb") as model_file:
                 _, web_url = file_storage.save_stream(model_file, os.path.basename(local_model_path), "uploads/models")
            
            # Success
            job_repo.update_job_status(job_id, "COMPLETE", output_url=web_url)
            print(f"Job {job_id} completed: {web_url}")
            
        finally:
            if os.path.exists(front_path): os.remove(front_path)
            if os.path.exists(side_path): os.remove(side_path)
            if os.path.exists(local_model_path): os.remove(local_model_path)
        
    except Exception as e:
        print(f"Critical Error in Job {job_id}: {e}")
        job_repo.update_job_status(job_id, "FAILED")
    finally:
        db.close()
