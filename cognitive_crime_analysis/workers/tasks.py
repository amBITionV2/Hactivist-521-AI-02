import sys
import os
import json
import requests
from celery import Celery
from neo4j import GraphDatabase
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image
import fitz  # PyMuPDF

# --- App and Environment Setup ---
# Ensure the app's root directory is in the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
load_dotenv()

# --- Neo4j Connection Details ---
NEO4J_URI = "bolt://localhost:7687"
# IMPORTANT: Use a secure method for credentials in production
NEO4J_AUTH = ("neo4j", "Crime2*graph") 

# --- Gemini API Details ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY environment variable not set.")
    
genai.configure(api_key=GEMINI_API_KEY)


def get_neo4j_driver():
    """Establishes and returns a connection to the Neo4j database."""
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def extract_knowledge_from_text(text: str):
    """
    Uses the Gemini model to perform advanced entity and pattern extraction.
    This prompt is specifically designed for building a connected knowledge base.
    """
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Analyze the following crime report and extract a structured knowledge graph.

    Your goal is to identify unique entities and the relationships between them, formatted as a single JSON object.

    The JSON object must have three keys: "nodes", "relationships", and "summary".

    1.  **nodes**: A list of dictionaries. Each dictionary must have:
        - "id": A unique name for the entity (e.g., "Arthur Vance").
        - "label": The type of entity. Use one of the following labels:
          'Person', 'Location', 'Organization', 'Date', 'Time', 'Evidence', 'Weapon', 'Vehicle', 'CrimeType', 'Pattern'.
        - "properties": A dictionary of key-value pairs describing the entity (e.g., {{"alias": "The Ghost", "description": "Approx. 6'1\", slender build, spiderweb tattoo on left hand"}}).

    2.  **relationships**: A list of dictionaries. Each dictionary must have:
        - "source": The "id" of the source node.
        - "target": The "id" of the target node.
        - "type": The relationship type in uppercase SNAKE_CASE (e.g., 'HAS_SUSPECT', 'OCCURRED_AT', 'USED_WEAPON').

    3.  **summary**: A dictionary containing:
        - "crime_type": The primary classification of the crime (e.g., "Armed Robbery").
        - "pattern": A description of the Modus Operandi (M.O.) used (e.g., "Disables security systems before entry, targets high-value goods").

    **CRIME REPORT TEXT:**
    ---
    {text}
    ---

    **JSON OUTPUT:**
    """
    
    response = model.generate_content(prompt)
    
    # Clean up the response to get a valid JSON object
    response_text = response.text
    clean_json_text = response_text.strip().replace('```json', '').replace('```', '')
    
    return json.loads(clean_json_text)


@celery_app.task(name="workers.tasks.process_uploaded_file_task")
def process_uploaded_file_task(case_id: int, file_content: bytes, filename: str, content_type: str):
    """
    Primary task that routes the uploaded file to the correct processor (text/pdf or image).
    """
    print(f"WORKER: Received file {filename} for case {case_id} with type {content_type}")
    
    # --- Route to Text/PDF Processor ---
    if content_type in ['text/plain', 'application/pdf']:
        extracted_text = ""
        if content_type == 'text/plain':
            extracted_text = file_content.decode('utf-8')
        elif content_type == 'application/pdf':
            try:
                with fitz.open(stream=file_content, filetype="pdf") as doc:
                    for page in doc:
                        extracted_text += page.get_text()
            except Exception as e:
                print(f"WORKER: Failed to extract text from PDF for case {case_id}. Error: {e}")
                # Update status to failed in DB
                return
        
        if extracted_text:
            print(f"WORKER: Text extracted successfully. Sending to knowledge base task.")
            build_knowledge_base_from_text_task.delay(case_id, extracted_text)
        else:
            print(f"WORKER: No text could be extracted from {filename} for case {case_id}.")

    # --- Route to Image Processor ---
    elif 'image' in content_type:
        # For image analysis, we need to save the file temporarily so PIL can open it.
        temp_dir = "temp_uploads"
        os.makedirs(temp_dir, exist_ok=True)
        temp_file_path = os.path.join(temp_dir, filename)
        with open(temp_file_path, "wb") as f:
            f.write(file_content)
            
        print(f"WORKER: Image saved temporarily. Sending to image analysis task.")
        analyze_image_task.delay(case_id, temp_file_path)
    
    else:
        print(f"WORKER: Unsupported file type for case {case_id}: {content_type}")


@celery_app.task(name="workers.tasks.build_knowledge_base_from_text_task")
def build_knowledge_base_from_text_task(case_id: int, text_content: str):
    """
    Processes extracted text to build a unified, interconnected knowledge graph in Neo4j.
    """
    print(f"WORKER: Starting knowledge base construction for case_id: {case_id}")
    driver = None
    try:
        # 1. Use Gemini to get structured knowledge data
        knowledge_data = extract_knowledge_from_text(text_content)
        nodes = knowledge_data.get("nodes", [])
        relationships = knowledge_data.get("relationships", [])
        summary = knowledge_data.get("summary", {})
        
        print(f"WORKER: Extracted {len(nodes)} nodes and {len(relationships)} relationships.")

        # 2. Write to Neo4j using the MERGE strategy
        if nodes or relationships:
            driver = get_neo4j_driver()
            with driver.session() as session:
                # A. MERGE the Case node itself
                session.run("MERGE (c:Case {case_id: $case_id})", case_id=case_id)

                # B. MERGE all extracted nodes (People, Locations, etc.)
                for node in nodes:
                    # The MERGE command is key: it finds the node or creates it, preventing duplicates.
                    cypher_query = f"""
                        MERGE (n:{node['label']} {{id: $id}})
                        SET n += $properties
                    """
                    session.run(cypher_query, id=node['id'], properties=node.get('properties', {}))

                # C. Create relationships between the new nodes
                for rel in relationships:
                    cypher_query = f"""
                        MATCH (source {{id: $source_id}})
                        MATCH (target {{id: $target_id}})
                        MERGE (source)-[:{rel['type']}]->(target)
                    """
                    session.run(cypher_query, source_id=rel['source'], target_id=rel['target'])

                # D. Connect the Case to key summary nodes (CrimeType and Pattern)
                if summary.get('crime_type'):
                    session.run("""
                        MATCH (c:Case {case_id: $case_id})
                        MERGE (ct:CrimeType {type: $crime_type})
                        MERGE (c)-[:IS_A]->(ct)
                    """, case_id=case_id, crime_type=summary['crime_type'])

                if summary.get('pattern'):
                    session.run("""
                        MATCH (c:Case {case_id: $case_id})
                        MERGE (p:Pattern {description: $pattern})
                        MERGE (c)-[:EXHIBITS]->(p)
                    """, case_id=case_id, pattern=summary['pattern'])
            
            print(f"WORKER: Successfully updated Neo4j knowledge base for case {case_id}.")

    except Exception as e:
        print(f"WORKER: An error occurred during knowledge base construction for case {case_id}: {e}")
        # Update PostgreSQL status to 'failed'
        return {"status": "Failed", "error": str(e)}
    finally:
        if driver:
            driver.close()

    # 3. Update case status in PostgreSQL to 'complete'
    from app.database import SessionLocal
    from app.models import Case
    db = SessionLocal()
    try:
        case_to_update = db.query(Case).filter(Case.id == case_id).first()
        if case_to_update:
            case_to_update.status = "complete"
            db.commit()
            print(f"WORKER: Updated status to 'complete' for case_id: {case_id}")
    finally:
        db.close()

    return {"status": "Complete"}


@celery_app.task(name="workers.tasks.analyze_image_task")
def analyze_image_task(case_id: int, file_path: str):
    """
    Sends an image to Gemini for analysis and stores the result.
    """
    print(f"WORKER: Starting IMAGE analysis for case_id: {case_id}")
    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        img = Image.open(file_path)
        prompt = "Analyze this crime scene photo. Describe any potential evidence, points of interest, or unusual details you observe. Be objective and factual."
        
        response = model.generate_content([prompt, img])
        analysis_text = response.text

        # Store the analysis in the PostgreSQL database
        from app.database import SessionLocal
        from app.models import Case
        db = SessionLocal()
        try:
            case_to_update = db.query(Case).filter(Case.id == case_id).first()
            if case_to_update:
                case_to_update.status = "complete"
                case_to_update.image_analysis = analysis_text
                db.commit()
                print(f"WORKER: Stored image analysis for case_id: {case_id}")
        finally:
            db.close()

    except Exception as e:
        print(f"WORKER: An error occurred during image analysis for case {case_id}: {e}")
        # Optionally, update status to 'failed'
        return {"status": "Failed", "error": str(e)}
    finally:
        # Clean up the temporary image file
        if os.path.exists(file_path):
            os.remove(file_path)

    print(f"WORKER: Finished image analysis for case_id: {case_id}")
    return {"status": "Complete"}
