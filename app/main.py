# Add these imports at the top
from fastapi import FastAPI, Depends, UploadFile, File
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from workers.tasks import process_case_file_task # <-- IMPORT THE TASK

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Cognitive Crime Analysis System API")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    return {"status": "API is running locally"}

# This endpoint is the same as before
@app.post("/cases/", response_model=schemas.Case)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db)):
    db_case = models.Case(filename=case.filename)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case

# --- NEW ENDPOINT ---
@app.post("/upload-case/")
def upload_and_process_case(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """
    Upload a file, create a case record, and dispatch a background task for processing.
    """
    # 1. Create a case record in PostgreSQL
    db_case = models.Case(filename=file.filename, status="processing")
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    # 2. Dispatch the background processing task
    # Note: We can't send the whole file object, so we send the info needed to process it.
    # In a real app, you'd save the file to disk/S3 first.
    process_case_file_task.delay(db_case.id, db_case.filename)
    
    # 3. Respond to the user immediately
    return {"message": "File uploaded and is being processed in the background.", "case_id": db_case.id}