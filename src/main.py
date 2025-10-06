from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from . import crud, models, schemas
from .database import SessionLocal, engine

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/models/", response_model=schemas.Model, status_code=201)
def create_new_model(model: schemas.ModelCreate, db: Session = Depends(get_db)):
    return crud.create_model(db=db, model=model)


@app.get("/models/", response_model=List[schemas.Model])
def read_all_models(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    models = crud.get_models(db, skip=skip, limit=limit)
    return models


@app.get("/models/{model_id}", response_model=schemas.Model)
def read_one_model(model_id: int, db: Session = Depends(get_db)):
    db_model = crud.get_model(db, model_id=model_id)
    if db_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return db_model


@app.put("/models/{model_id}", response_model=schemas.Model)
def update_model_status_endpoint(model_id: int, status: str, output_url: str = None, db: Session = Depends(get_db)):
    updated_model = crud.update_model_status(db, model_id=model_id, status=status, output_url=output_url)
    if updated_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return updated_model
    

@app.delete("/models/{model_id}", response_model=schemas.Model)
def delete_existing_model(model_id: int, db: Session = Depends(get_db)):
    deleted_model = crud.delete_model(db, model_id=model_id)
    if deleted_model is None:
        raise HTTPException(status_code=404, detail="Model not found")
    return deleted_model