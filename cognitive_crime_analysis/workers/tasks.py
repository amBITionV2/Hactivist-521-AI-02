# workers/tasks.py (Upgraded)
import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import json
import requests
from celery import Celery
from neo4j import GraphDatabase
from dotenv import load_dotenv
import google.generativeai as genai
from PIL import Image

# --- App and Environment Setup ---
celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
load_dotenv()

# --- Neo4j Connection Details ---
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "Crime2*graph") # Remember to set your password

# --- Gemini API Details ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_API_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

def extract_graph_from_text(text: str):
    """Uses Gemini to extract entities and relationships from text."""
    prompt = f"""
    Analyze the following crime report text. Extract the key entities (people, places, organizations, dates, times, objects) and the relationships between them.
    Return the result as a JSON object with two keys: "entities" and "relationships".
    - "entities" should be a list of objects, each with a "name" and "type".
    - "relationships" should be a list of objects, each with a "source" (entity name), "target" (entity name), and "type" (the relationship, e.g., WITNESSED_AT, FLED_TOWARDS).
    - Use uppercase snake_case for relationship types.

    Text: "{text}"

    JSON Output:
    """
    
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(GEMINI_API_URL, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    
    # Clean up the response to get a valid JSON object
    response_text = response.json()['candidates'][0]['content']['parts'][0]['text']
    clean_json_text = response_text.strip().replace('```json', '').replace('```', '')
    
    return json.loads(clean_json_text)


@celery_app.task
def process_case_file_task(case_id: int, file_content: str):
    print(f"WORKER: Starting ADVANCED graph extraction for case_id: {case_id}")
    
    try:
        # 1. Use Gemini to get structured graph data
        graph_data = extract_graph_from_text(file_content)
        entities = graph_data.get("entities", [])
        relationships = graph_data.get("relationships", [])
        print(f"WORKER: Extracted {len(entities)} entities and {len(relationships)} relationships.")

        # 2. Write graph to Neo4j
        if entities or relationships:
            driver = get_neo4j_driver()
            with driver.session() as session:
                # Create a single Case node
                session.run("MERGE (c:Case {case_id: $case_id})", case_id=case_id)

                # Create all entity nodes and link them to the Case
                for entity in entities:
                    session.run("""
                        MERGE (c:Case {case_id: $case_id})
                        MERGE (e:Entity {name: $name, type: $type})
                        MERGE (e)-[:BELONGS_TO]->(c)
                    """, case_id=case_id, name=entity['name'], type=entity['type'])

                # Create all relationships between entities
                for rel in relationships:
                    session.run("""
                        MATCH (source:Entity {name: $source_name})
                        MATCH (target:Entity {name: $target_name})
                        MERGE (source)-[:""" + rel['type'] + """]->(target)
                    """, source_name=rel['source'], target_name=rel['target'])
            driver.close()
            print(f"WORKER: Successfully wrote smart graph to Neo4j for case {case_id}.")

    except Exception as e:
        print(f"WORKER: An error occurred during processing for case {case_id}: {e}")
        # Optionally, update the case status to 'failed' in PostgreSQL
        return {"status": "Failed", "error": str(e)}

    # Update case status in PostgreSQL to 'complete' (code from before)
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

    print(f"WORKER: Finished processing for case_id: {case_id}")
    return {"status": "Complete"}

@celery_app.task
def analyze_image_task(case_id: int, file_path: str):
    """
    Sends an image to Gemini for analysis and stores the result.
    """
    print(f"WORKER: Starting IMAGE analysis for case_id: {case_id}")
    try:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found.")

        genai.configure(api_key=api_key)

        # Use a model that supports vision
        model = genai.GenerativeModel('gemini-2.5-flash')

        img = Image.open(file_path)
        prompt = "Analyze this crime scene photo. Describe any potential evidence, points of interest, or unusual details you observe. Be objective and factual."

        # Send the prompt and the image to the model
        response = model.generate_content([prompt, img])
        analysis_text = response.text

        # Store the analysis in the database
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

    print(f"WORKER: Finished image analysis for case_id: {case_id}")
    return {"status": "Complete"}