from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class Model(Base):
    __tablename__ = "models"

    id = Column(Integer, primary_key=True, index=True)

    status = Column(String(50), nullable=False, default="PENDING")

    input_side_image_url_ = Column(String(255), nullable=False)

    input_front_image_url = Column(String(255), nullable=False)

    output_model_url = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    updated_at = Column(DateTime(timezone=True), onupdate=func.now())