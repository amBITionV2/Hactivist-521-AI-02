# Add these imports at the top
import os
import requests
import json
from dotenv import load_dotenv
from neo4j import GraphDatabase
from fastapi import FastAPI, Depends, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import models, schemas
from .database import SessionLocal, engine
from workers.tasks import process_case_file_task # <-- IMPORT THE TASK
from .api import detective
from typing import List

# --- Load environment variables from .env file ---
load_dotenv()

# --- Add Neo4j connection details here as well ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "Crime2*graph")


models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="Cognitive Crime Analysis System API")
app.include_router(detective.router)

origins = [
    "http://localhost:5173", # The address of our React app
    "http://localhost:3000", # A common alternative for React apps
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
# app/main.py

# ... (all the other imports and code stay the same) ...

# --- MODIFIED ENDPOINT ---
@app.post("/upload-case/")
async def upload_and_process_case(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """
    Upload a file, create a case record, and dispatch a background task for processing.
    """
    # 1. Create a case record in PostgreSQL
    db_case = models.Case(filename=file.filename, status="processing")
    db.add(db_case)
    db.commit()
    db.refresh(db_case)
    
    # 2. Read the file content
    file_content_bytes = await file.read()
    file_content_str = file_content_bytes.decode('utf-8')

    # 3. Dispatch the background processing task WITH the file content
    process_case_file_task.delay(db_case.id, file_content_str)
    
    # 4. Respond to the user immediately
    return {"message": "File uploaded and is being processed in the background.", "case_id": db_case.id}

@app.post("/cases/{case_id}/simulate")
def create_simulation(case_id: int):
    """
    Generates a crime narrative simulation using entities from the knowledge graph.
    """
    # 1. Fetch entities for the specific case from Neo4j
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

    # 2. Call the Gemini API
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
    
@app.get("/cases/", response_model=List[schemas.Case])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """
    Retrieve all case records from the database.
    """
    cases = db.query(models.Case).offset(skip).limit(limit).all()
    return cases

# app/main.py - Add this new endpoint

# ... (all your existing code and imports) ...

@app.get("/cases/{case_id}/graph")
def get_case_graph(case_id: int):
    """
    Retrieves all nodes and relationships for a specific case to be visualized.
    """
    nodes = []
    edges = []
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        # Query to get all entities belonging to the case
        result = session.run("""
            MATCH (e:Entity)-[:BELONGS_TO]->(c:Case {case_id: $case_id})
            RETURN id(e) AS id, e.name AS label, e.type AS type
        """, case_id=case_id)

        node_map = {}
        for record in result:
            node_data = {"id": record["id"], "label": record["label"], "group": record["type"]}
            nodes.append(node_data)
            node_map[record["id"]] = node_data

        # Query to get all relationships between the entities of this case
        result = session.run("""
            MATCH (e1:Entity)-[:BELONGS_TO]->(c:Case {case_id: $case_id})
            MATCH (e2:Entity)-[:BELONGS_TO]->(c)
            MATCH (e1)-[r]->(e2)
            WHERE NOT type(r) = 'BELONGS_TO'
            RETURN id(e1) AS from, id(e2) AS to, type(r) AS label
        """, case_id=case_id)

        for record in result:
            edges.append({"from": record["from"], "to": record["to"], "label": record["label"]})

    driver.close()
    return {"nodes": nodes, "edges": edges}