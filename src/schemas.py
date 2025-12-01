from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

# Schemas for the Part model
class PartBase(BaseModel):
    name: str
    sku: str
    side_image_url: str
    front_image_url: str

class PartCreate(PartBase):
    pass

class Part(PartBase):
    id: int
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Schemas for the ComparisonJob model
class ComparisonJobBase(BaseModel):
    part_id: int
    input_front_image_url: str
    input_side_image_url: str

class ComparisonJobCreate(ComparisonJobBase):
    pass

class ComparisonJob(ComparisonJobBase):
    id: int
    status: str
    output_model_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
        
class JobResponse(BaseModel):
    jobId: str

class JobStatusResponse(BaseModel):
    status: str
    modelUrl: Optional[str] = None

class DashboardStats(BaseModel):
    totalParts: int
    totalAnalyses: int
    activeComparisons: int


class DefectBox(BaseModel):
    x: int
    y: int
    width: int
    height: int
    type: str
    area: float

class DefectAnalysisResponse(BaseModel):
    total_defects: int
    image_dimensions: dict
    defects: List[DefectBox]