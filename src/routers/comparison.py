from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from ..domain import schemas
from ..repositories.interfaces import IJobCreator, IJobRetriever, IJobUpdater
from ..core.dependencies import get_job_repository, get_file_storage
from ..services.storage import IFileStorage
from ..workers.tasks import process_job_3d_generation

router = APIRouter(
    prefix="/api/compare",
    tags=["comparison"]
)

@router.post("/", response_model=schemas.ComparisonJob)
async def create_and_run_comparison(
    background_tasks: BackgroundTasks,
    job_creator: IJobCreator = Depends(get_job_repository),
    file_storage: IFileStorage = Depends(get_file_storage),
    reference_part_id: int = Form(...), 
    front_image: UploadFile = File(...), 
    side_image: UploadFile = File(...)  
):
    # 1. Read bytes
    front_bytes = await front_image.read()
    side_bytes = await side_image.read()
    
    # 2. Save inputs
    INPUT_DIR = "uploads/inputs"
    # Using prefix="job" to distinguish files
    _, front_url = file_storage.save(front_bytes, front_image.filename, INPUT_DIR, prefix="job")
    _, side_url = file_storage.save(side_bytes, side_image.filename, INPUT_DIR, prefix="job")

    # 3. Create Job PENDING
    job_schema = schemas.ComparisonJobCreate(
        part_id=reference_part_id,
        input_front_image_url=front_url,
        input_side_image_url=side_url
    )
    db_job = job_creator.create_job(job=job_schema)

    # 4. Trigger Heavy Task
    background_tasks.add_task(
        process_job_3d_generation, 
        db_job.id, 
        front_url, 
        side_url  
    )

    return db_job

@router.get("/status/{job_id}", response_model=schemas.JobStatusResponse)
def get_job_status(job_id: int, job_retriever: IJobRetriever = Depends(get_job_repository)):
    job = job_retriever.get_job(job_id=job_id)
    
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return {
        "status": job.status.lower(),
        "modelUrl": job.output_model_url
    }

@router.put("/{job_id}/status", response_model=schemas.ComparisonJob)
def update_job_status_final(job_id: int, new_status: str = None, job_repo: IJobUpdater = Depends(get_job_repository)):
    """
    Updates the status of a comparison job to APPROVED or REJECTED.
    """
    
    updated_job = job_repo.update_job_status(job_id, new_status.upper())
    if updated_job is None:
        raise HTTPException(status_code=404, detail="Comparison Job not found")
        
    return updated_job
