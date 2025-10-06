from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ModelBase(BaseModel):
    input_side_image_url: str
    input_front_image_url: str

class ModelCreate(ModelBase):
    pass

class Model(ModelBase):
    id: int
    status: str
    output_model_url: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True