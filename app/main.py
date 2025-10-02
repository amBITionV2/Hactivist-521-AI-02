from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine

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

@app.post("/cases/", response_model=schemas.Case)
def create_case(case: schemas.CaseCreate, db: Session = Depends(get_db)):
    """
    Create a new case record in the database.
    This will be used to track uploaded files.
    """
    db_case = models.Case(filename=case.filename)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    return db_case