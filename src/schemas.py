from pydantic import BaseModel
from typing import Optional
from datetime import datetime

# Schemas for the Part model
class PartBase(BaseModel):
    name: str
    sku: str
    main_image_url: str
    secondary_image_url: Optional[str] = None

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