from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from workers.tasks import process_case_file # <-- IMPORT THE TASK

# This line tells SQLAlchemy to create the tables defined in models.py
# It will create the 'cases' table in your 'crime_db' the first time the app runs.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cognitive Crime Analysis System API")

# Dependency: Manages database sessions for each request
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def read_root():
    """A simple endpoint to check if the API is running."""
    return {"status": "API is running locally"}

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