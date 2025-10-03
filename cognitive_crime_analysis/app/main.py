import shutil
import os
import requests
import json
from dotenv import load_dotenv
from typing import List, Optional
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from neo4j import GraphDatabase
from fastapi.staticfiles import StaticFiles
from .api import detective 
from . import models, schemas
from .database import SessionLocal, engine
from workers.tasks import process_case_file_task, analyze_image_task

# Load environment variables from .env file
load_dotenv()

# This creates the tables in your database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Cognitive Crime Analysis System API")

# --- CORS middleware ---
origins = [
    "http://localhost:5173",
    "http://localhost:3000",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Neo4j Connection Details ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD", "Crime2*graph")) # Remember to set your password

# --- Dependency to get a database session ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---
@app.get("/")
def read_root():
    return {"status": "API is running locally"}

@app.get("/cases/", response_model=List[schemas.Case])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    cases = db.query(models.Case).order_by(models.Case.id.desc()).offset(skip).limit(limit).all()
    return cases

@app.post("/upload-case/")
async def upload_and_process_case(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """
    Saves uploaded file, creates a case record, and dispatches the correct background task.
    """
    # 1. Save the file to the 'uploads' directory
    file_location = f"uploads/{file.filename}"
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    # 2. Create a case record in PostgreSQL
    db_case = models.Case(filename=file.filename, status="processing", file_path=file_location)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # 3. Decide which worker to call based on file type
    file_extension = file.filename.split('.')[-1].lower()
    if file_extension in ['txt', 'md', 'log']:
        # ONLY read content if it's a text file
        with open(file_location, "r", encoding='utf-8') as f:
            content = f.read()
        process_case_file_task.delay(db_case.id, content)
    elif file_extension in ['png', 'jpg', 'jpeg', 'webp', 'gif', 'bmp']:
        # For images, just send the file path
        analyze_image_task.delay(db_case.id, file_location)
    else:
        db_case.status = "failed"
        db.commit()
        return {"message": "Unsupported file type.", "case_id": db_case.id}

    return {"message": "File uploaded and is being processed.", "case_id": db_case.id}

@app.post("/cases/{case_id}/simulate")
def create_simulation(case_id: int):
    """
    Generates a crime narrative simulation using entities from the knowledge graph.
    """
    entities = []
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        result = session.run("""
            MATCH (e:Entity)-[:BELONGS_TO]->(c:Case {case_id: $case_id})
            RETURN e.name AS name, e.type AS type
        """, case_id=case_id)
        for record in result:
            entities.append(f"{record['name']} ({record['type']})")
    driver.close()

    if not entities:
        return {"error": "No entities found for this case. Ensure the file has been processed."}

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return {"error": "GEMINI_API_KEY not found. Please set it in your .env file."}
    
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
    
    entity_list_str = ", ".join(entities)
    prompt = (f"You are a crime analyst. Based on the following key entities extracted from a case file, "
              f"generate a plausible, step-by-step narrative of how the crime likely occurred. "
              f"Weave the entities naturally into the story.\n\nKey Entities: {entity_list_str}\n\nNarrative:")
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    
    if response.status_code == 200:
        result = response.json()
        narrative = result['candidates'][0]['content']['parts'][0]['text']
        return {"case_id": case_id, "simulation": narrative}
    else:
        return {"error": "Failed to generate simulation from Gemini API.", "details": response.text}

# app/main.py - Replace the get_case_graph function

@app.get("/cases/{case_id}/graph")
def get_case_graph(case_id: int):
    """
    Retrieves all nodes AND relationships for a specific case to be visualized.
    """
    nodes = []
    edges = []
    node_ids = set() # Use a set to track which nodes are part of this case

    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        # Step 1: Get all entities for the case and add them as nodes
        result = session.run("""
            MATCH (e:Entity)-[:BELONGS_TO]->(c:Case {case_id: $case_id})
            RETURN id(e) AS id, e.name AS label, e.type AS group
        """, case_id=case_id)
        
        for record in result:
            nodes.append({"id": record["id"], "label": record["label"], "group": record["group"]})
            node_ids.add(record["id"])

        # Step 2: Get all relationships BETWEEN the nodes we just found
        result = session.run("""
            MATCH (source)-[r]->(target)
            WHERE id(source) IN $node_ids AND id(target) IN $node_ids AND NOT type(r) = 'BELONGS_TO'
            RETURN id(source) AS `from`, id(target) AS `to`, type(r) AS label
        """, node_ids=list(node_ids))

        for record in result:
            edges.append({"from": record["from"], "to": record["to"], "label": record["label"]})
    
    driver.close()
    return {"nodes": nodes, "edges": edges}

# Mount the 'uploads' directory to serve static files (images)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.include_router(detective.router)