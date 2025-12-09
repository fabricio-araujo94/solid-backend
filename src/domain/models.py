from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from ..core.database import Base

class Part(Base):
    """
    Represents a standard part in the system, used as a reference for quality control.
    """
    __tablename__ = "parts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    side_image_url = Column(String(255), nullable=False)
    front_image_url = Column(String(255), nullable=False)
    
    model_3d_url = Column(String(255), nullable=False, default="./examples/key.stl")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # This creates a link to easily access all comparison jobs associated with this part.
    comparison_jobs = relationship("ComparisonJob", back_populates="part")


class ComparisonJob(Base):
    """
    Represents an asynchronous job to generate a 3D model from uploaded images
    and compare it against a standard part.
    """
    __tablename__ = "comparison_jobs"

    id = Column(Integer, primary_key=True, index=True)

    # Foreign key to link this job to a specific Part
    part_id = Column(Integer, ForeignKey("parts.id"), nullable=False)

    status = Column(String(50), nullable=False, default="pending")
    input_side_image_url = Column(String(255), nullable=False)
    input_front_image_url = Column(String(255), nullable=False)
    output_model_url = Column(String(255), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # This creates a link back to the Part object.
    part = relationship("Part", back_populates="comparison_jobs")