import os
import json
import requests
from dotenv import load_dotenv
from typing import List
from fastapi import FastAPI, Depends, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from neo4j import GraphDatabase
from fastapi.staticfiles import StaticFiles

# --- Local Imports ---
# This structure assumes 'api', 'models', etc., are in the same 'app' directory
from .api import detective 
from . import models, schemas
from .database import SessionLocal, engine
# Updated worker import to reflect the new primary task
from workers.tasks import process_uploaded_file_task

# --- Initial Setup ---
load_dotenv()
models.Base.metadata.create_all(bind=engine) # Create database tables on startup

app = FastAPI(title="Cognitive Crime Analysis System API")

# --- CORS Middleware ---
# Allows the React frontend to communicate with this API
origins = ["http://localhost:5173", "http://localhost:3000"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Neo4j Connection Details ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", os.getenv("NEO4J_PASSWORD", "Crime2*graph"))

# --- Database Dependency ---
def get_db():
    """Dependency to get a SQLAlchemy session for each request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@app.get("/")
def read_root():
    return {"status": "API is running"}

@app.get("/cases/", response_model=List[schemas.Case])
def read_cases(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    """Retrieves a list of all cases from the PostgreSQL database."""
    cases = db.query(models.Case).order_by(models.Case.id.desc()).offset(skip).limit(limit).all()
    return cases

@app.post("/upload-case/")
async def upload_and_process_case(db: Session = Depends(get_db), file: UploadFile = File(...)):
    """
    Handles file uploads, creates a case record, and dispatches a background task.
    This endpoint is now much simpler, as the worker handles all file-type logic.
    """
    # 1. Read the file content into memory once.
    file_content = await file.read()
    
    # 2. Define the path for static file serving (for images) but don't save text files.
    # This ensures the frontend can access uploaded images later.
    uploads_dir = "uploads"
    os.makedirs(uploads_dir, exist_ok=True)
    file_path = os.path.join(uploads_dir, file.filename)

    # 3. Create a case record in PostgreSQL.
    db_case = models.Case(filename=file.filename, status="processing", file_path=file_path)
    db.add(db_case)
    db.commit()
    db.refresh(db_case)

    # 4. Save the file ONLY if it's an image, as it needs to be served.
    # Text/PDF content is passed directly to the worker and doesn't need to be stored here.
    if "image" in file.content_type:
        with open(file_path, "wb") as f:
            f.write(file_content)

    # 5. Dispatch the single, unified background task.
    # The worker will handle whether it's a PDF, TXT, or Image.
    process_uploaded_file_task.delay(
        case_id=db_case.id,
        file_content=file_content,
        filename=file.filename,
        content_type=file.content_type
    )

    return {"message": "File is being processed in the background.", "case_id": db_case.id}

@app.get("/cases/{case_id}/graph")
def get_case_graph(case_id: int):
    """
    Retrieves the specific knowledge graph for a single case for visualization.
    This query is designed for the new, unified graph model.
    """
    nodes = []
    edges = []
    node_ids = set()
    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            # Step 1: Find all nodes directly or indirectly related to the case.
            # This includes Persons, Locations, Patterns, etc.
            result = session.run("""
                MATCH (c:Case {case_id: $case_id})-[*1..2]-(related_node)
                WHERE NOT related_node:Case
                WITH COLLECT(DISTINCT related_node) AS nodes_in_case
                UNWIND nodes_in_case AS n
                RETURN id(n) AS id, n.id AS label, labels(n)[0] AS group, n as properties
            """, case_id=case_id)
            
            for record in result:
                node_data = {
                    "id": record["id"],
                    "label": record["label"],
                    "group": record["group"],
                    "title": json.dumps(record["properties"], indent=2) # Tooltip for UI
                }
                nodes.append(node_data)
                node_ids.add(record["id"])

            # Step 2: Get all relationships BETWEEN the nodes we just found.
            if node_ids:
                result = session.run("""
                    MATCH (source)-[r]->(target)
                    WHERE id(source) IN $node_ids AND id(target) IN $node_ids
                    RETURN id(source) AS `from`, id(target) AS `to`, type(r) AS label
                """, node_ids=list(node_ids))

                for record in result:
                    edges.append({"from": record["from"], "to": record["to"], "label": record["label"]})
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection error: {e}")
    finally:
        if driver:
            driver.close()

    return {"nodes": nodes, "edges": edges}

@app.get("/cases/{case_id}/related")
def get_related_cases(case_id: int):
    """
    Finds other cases related to the given case by shared suspects, M.O., or crime type.
    This is the core endpoint for the interconnected knowledge base.
    """
    related_cases_data = []
    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            # This query uses OPTIONAL MATCH to find connections across different paths.
            query = """
                MATCH (c1:Case {case_id: $case_id})
                
                // Find cases with a shared suspect
                OPTIONAL MATCH (c1)-[*1..2]-(p:Person)-[*1..2]-(c2:Case)
                WHERE c1 <> c2
                WITH c1, collect(DISTINCT {case_id: c2.case_id, reason: 'Shared Person', detail: p.id}) AS person_cases
                
                // Find cases with a shared M.O. (Pattern)
                OPTIONAL MATCH (c1)-[:EXHIBITS]->(pattern:Pattern)<-[:EXHIBITS]-(c3:Case)
                WHERE c1 <> c3
                WITH c1, person_cases, collect(DISTINCT {case_id: c3.case_id, reason: 'Shared M.O.', detail: pattern.description}) AS pattern_cases
                
                RETURN person_cases + pattern_cases AS all_related_cases
            """
            result = session.run(query, case_id=case_id)
            data = result.single()
            if data:
                # Use a dictionary to merge results and avoid duplicates
                merged_results = {}
                for item in data['all_related_cases']:
                    cid = item['case_id']
                    if cid not in merged_results:
                        merged_results[cid] = {'case_id': cid, 'connections': []}
                    merged_results[cid]['connections'].append({'reason': item['reason'], 'detail': item['detail']})
                related_cases_data = list(merged_results.values())

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Neo4j connection error: {e}")
    finally:
        if driver:
            driver.close()
            
    return {"related_cases": related_cases_data}


@app.post("/cases/{case_id}/simulate")
def create_simulation(case_id: int):
    """
    Generates a crime narrative simulation using entities from the knowledge graph.
    Updated to work with the new graph model.
    """
    entity_list = []
    driver = None
    try:
        driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
        with driver.session() as session:
            result = session.run("""
                MATCH (c:Case {case_id: $case_id})-[*1..2]-(n)
                WHERE NOT n:Case
                RETURN DISTINCT n.id as name, labels(n)[0] as type
            """, case_id=case_id)
            for record in result:
                if record["name"]:
                    entity_list.append(f"{record['name']} ({record['type']})")

        if not entity_list:
            raise HTTPException(status_code=404, detail="No entities found for this case. Ensure the file has been processed.")

        # --- Call Gemini API for Simulation ---
        api_key = os.getenv("GEMINI_API_KEY")
        api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={api_key}"
        
        entity_list_str = ", ".join(entity_list)
        prompt = (f"You are a crime analyst. Based on the following key entities extracted from a case file, "
                  f"generate a plausible, step-by-step narrative of how the crime likely occurred. "
                  f"Weave the entities naturally into the story.\n\nKey Entities: {entity_list_str}\n\nNarrative:")
        
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        
        response = requests.post(api_url, headers=headers, data=json.dumps(payload))
        response.raise_for_status()

        result_json = response.json()
        narrative = result_json['candidates'][0]['content']['parts'][0]['text']
        return {"case_id": case_id, "simulation": narrative}

    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Failed to call Gemini API: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {e}")
    finally:
        if driver:
            driver.close()


# --- Static File Serving & Sub-Routers ---
# This allows the frontend to access images stored in the 'uploads' directory
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
# Include the routes from the detective.py file (for chat, image generation, etc.)
app.include_router(detective.router)
