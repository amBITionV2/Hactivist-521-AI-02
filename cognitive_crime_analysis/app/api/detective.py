import os
import json
import requests
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from neo4j import GraphDatabase
from dotenv import load_dotenv

# --- Database Integration ---
# We need to import these to update our case table with the new image
from app.database import SessionLocal
from app.models import Case
from sqlalchemy.orm import Session

# Load environment variables from .env file
load_dotenv()

# --- Configuration ---
router = APIRouter()
NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "Crime2*graph") # Remember to set your password
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# --- Pydantic Models ---
class QuestionRequest(BaseModel):
    question: str

class SuspectImageRequest(BaseModel):
    description: str

# Dependency to get a database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- API Endpoints ---

@router.post("/cases/{case_id}/ask", tags=["Detective"])
@router.post("/cases/{case_id}/ask", tags=["Detective"])
def ask_ai_detective(case_id: int, request: QuestionRequest):
    """
    Answers a user's question by reasoning about the context of a case's knowledge graph.
    """
    # 1. Retrieve context from the knowledge graph (this part is the same)
    context_items = []
    driver = GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)
    with driver.session() as session:
        result = session.run("""
            MATCH (e1:Entity)-[:BELONGS_TO]->(c:Case {case_id: $case_id})
            OPTIONAL MATCH (e1)-[r]->(e2:Entity) WHERE NOT type(r) = 'BELONGS_TO'
            RETURN e1.name as entity1, type(r) as relation, e2.name as entity2
        """, case_id=case_id)
        for record in result:
            if record["relation"]:
                context_items.append(f"- {record['entity1']} {record['relation'].replace('_', ' ')} {record['entity2']}.")
            else:
                context_items.append(f"- {record['entity1']} is an entity in this case.")
    driver.close()

    if not context_items:
        return {"answer": "I'm sorry, I don't have enough information about this case to answer."}

    # --- 2. THE NEW, SMARTER PROMPT ---
    context_str = "\n".join(set(context_items))
    prompt = f"""
    You are an expert AI detective. Your task is to analyze a set of known facts from a case's knowledge graph and answer a user's question.
    Use your reasoning abilities to connect the facts and infer logical conclusions, even if they are not explicitly stated.
    If the user asks for "clues", you should identify any piece of information that could be significant to an investigation (e.g., specific times, locations, objects, inconsistencies, or actions) and explain why it's a clue.
    Base your answer on the provided facts, but you are allowed to make logical deductions.

    **Known Facts from Knowledge Graph:**
    {context_str}

    **User's Question:**
    {request.question}

    **Your Detective Analysis:**
    """

    # 3. Call the Gemini API (this part is the same)
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not found."}
    
    api_url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt}]}]}
    headers = {'Content-Type': 'application/json'}
    
    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    
    result = response.json()
    answer = result['candidates'][0]['content']['parts'][0]['text']

    return {"answer": answer}

@router.post("/cases/{case_id}/generate-suspect-image", tags=["Detective"])
def generate_suspect_image(case_id: int, request: SuspectImageRequest, db: Session = Depends(get_db)):
    """
    Generates a suspect image using Imagen and saves the result to the case.
    """
    if not GEMINI_API_KEY:
        return {"error": "GEMINI_API_KEY not found."}

    # Use the recommended Imagen model for high-quality image generation
    # NEW, CORRECT LINE
    # NEW, CORRECTED LINE
    api_url = f"https://generativelanguage.googleapis.com/v1beta/models/imagen-3.0-generate-002:predict?key={GEMINI_API_KEY}"
    
    prompt = f"A realistic police sketch of a suspect. {request.description}"
    payload = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": 1}}
    headers = {'Content-Type': 'application/json'}

    response = requests.post(api_url, headers=headers, data=json.dumps(payload))
    response.raise_for_status()
    result = response.json()

    # The API returns the image as a base64 encoded string
    base64_image = result.get("predictions", [{}])[0].get("bytesBase64Encoded")
    if not base64_image:
        return {"error": "Failed to get image data from the API."}

    image_data_url = f"data:image/png;base64,{base64_image}"

    # Save the generated image URL to our database
    case_to_update = db.query(Case).filter(Case.id == case_id).first()
    if case_to_update:
        case_to_update.suspect_image = image_data_url
        db.commit()
    
    return {"suspect_image_url": image_data_url}

