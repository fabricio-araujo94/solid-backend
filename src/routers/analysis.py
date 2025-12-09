from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from ..domain import schemas
from ..core.dependencies import get_defect_service
from ..services.defect_service import DefectService

router = APIRouter(
    prefix="/api/analyze",
    tags=["analysis"]
)

@router.post("/defects", response_model=schemas.DefectAnalysisResponse)
async def analyze_defects(file: UploadFile = File(...), service: DefectService = Depends(get_defect_service)):
    contents = await file.read()
    try:
        result = service.analyze(contents)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
