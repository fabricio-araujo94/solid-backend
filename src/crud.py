from sqlalchemy.orm import Session
from . import models, schemas

def get_model(db: Session, model_id: int):
    return db.query(models.Model).filter(models.Model.id == model_id).first()

def get_models(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Model).offset(skip).limit(limit).all()

def create_model(db: Session, model: schemas.ModelCreate):

    db_model = models.Model(**model.model_dump())
    
    db.add(db_model)
    
    db.commit()
    
    db.refresh(db_model)
    
    return db_model


def update_model_status(db: Session, model_id: int, status: str, output_url: str = None):
    db_model = get_model(db, model_id=model_id)
    if db_model:
        db_model.status = status
        if output_url:
            db_model.output_model_url = output_url
        
        db.commit()
        db.refresh(db_model)
        return db_model
    return None


def delete_model(db: Session, model_id: int):
    db_model = get_model(db, model_id=model_id)
    if db_model:
        db.delete(db_model)
        db.commit()
        return db_model
    return None