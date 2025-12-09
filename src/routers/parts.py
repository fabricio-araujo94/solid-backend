from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from typing import List

from ..domain import schemas, models
from ..repositories.interfaces import IPartRepository, IPartReader, IPartWriter, IJobSearcher
from ..core.dependencies import get_part_repository, get_job_repository, get_file_storage
from ..services.storage import IFileStorage
from ..workers.tasks import process_part_3d_generation

router = APIRouter(
    prefix="/api/parts",
    tags=["parts"]
)

@router.post("/", response_model=schemas.Part, status_code=201)
async def create_new_part(
    background_tasks: BackgroundTasks,
    part_repo: IPartRepository = Depends(get_part_repository),
    file_storage: IFileStorage = Depends(get_file_storage),
    name: str = Form(...),
    sku: str = Form(...),
    side_image: UploadFile = File(...),
    front_image: UploadFile = File(...),
    part_type: str = Form("reference")
):
    
    db_part = part_repo.get_part_by_sku(sku=sku)
    if db_part:
        raise HTTPException(status_code=400, detail=f"SKU '{sku}' already registered.")

    front_bytes = await front_image.read()
    side_bytes = await side_image.read()
    
    STATIC_IMAGES_DIR = "static/images"
    
    _, side_url = file_storage.save(side_bytes, side_image.filename, STATIC_IMAGES_DIR)
    _, front_url = file_storage.save(front_bytes, front_image.filename, STATIC_IMAGES_DIR)

    part_data = schemas.PartCreate(
        name=name,
        sku=sku,
        side_image_url=side_url,
        front_image_url=front_url,
        part_type=part_type
    )
    new_part = part_repo.create_part(part=part_data)

    background_tasks.add_task(
        process_part_3d_generation,
        new_part.id,
        front_bytes,
        side_bytes
    )
    
    return new_part

@router.get("/", response_model=List[schemas.Part])
def read_all_parts(skip: int = 0, limit: int = 100, type: str = "reference", part_reader: IPartReader = Depends(get_part_repository)):
    return part_reader.get_parts(skip=skip, limit=limit, part_type=type)

@router.get("/{part_id}", response_model=schemas.Part)
def read_one_part(part_id: int, part_reader: IPartReader = Depends(get_part_repository)):
    db_part = part_reader.get_part(part_id=part_id)
    if db_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return db_part

@router.delete("/{part_id}", response_model=schemas.Part)
def delete_existing_part(part_id: int, part_writer: IPartWriter = Depends(get_part_repository)):
    deleted_part = part_writer.delete_part(part_id=part_id)
    if deleted_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    return deleted_part

@router.get("/{part_id}/jobs", response_model=List[schemas.ComparisonJob])
def read_jobs_by_part(part_id: int, 
                      part_reader: IPartReader = Depends(get_part_repository),
                      job_searcher: IJobSearcher = Depends(get_job_repository)):
    db_part = part_reader.get_part(part_id=part_id)
    if db_part is None:
        raise HTTPException(status_code=404, detail="Part not found")
    
    jobs = job_searcher.get_jobs_by_part(part_id=part_id)
    return jobs
