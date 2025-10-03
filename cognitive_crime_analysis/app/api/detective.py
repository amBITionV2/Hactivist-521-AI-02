"""
Detective agent endpoints for chat and suspect image generation using Gemini API.
"""
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import os
import requests

router = APIRouter()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_CHAT_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"
GEMINI_IMAGE_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro-vision:generateContent"

class ChatRequest(BaseModel):
    message: str
    case_file: str = None  # Optional: case file text
    suspect_description: str = None  # Optional: suspect description

class ChatResponse(BaseModel):
    reply: str
    clues: list[str]

class SuspectImageRequest(BaseModel):
    description: str

class SuspectImageResponse(BaseModel):
    image_url: str

@router.post("/detective/chat", response_model=ChatResponse)
def detective_chat(request: ChatRequest):
    """
    Chat with detective agent, generate clues using Gemini API.
    If suspect description is missing, prompt user for it.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not set.")
    # Try to extract suspect description from case file
    suspect_desc = request.suspect_description
    if not suspect_desc and request.case_file:
        # Simple extraction: look for lines containing 'suspect:'
        for line in request.case_file.split('\n'):
            if 'suspect:' in line.lower():
                suspect_desc = line.split(':', 1)[-1].strip()
                break
    prompt = f"Detective agent, analyze the following case and chat with the user. Generate clues and ask questions. Case: {request.case_file}\nUser: {request.message}"
    if not suspect_desc:
        prompt += "\nIf you need more information about the suspect, ask the user for a description."
    else:
        prompt += f"\nSuspect Description: {suspect_desc}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    response = requests.post(GEMINI_CHAT_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Gemini chat API error.")
    data = response.json()
    reply = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    clues = [line for line in reply.split("\n") if "clue" in line.lower()]
    return ChatResponse(reply=reply, clues=clues)

@router.post("/detective/suspect-image", response_model=SuspectImageResponse)
def generate_suspect_image(request: SuspectImageRequest):
    """
    Generate suspect image from description using Gemini API.
    """
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=500, detail="Gemini API key not set.")
    prompt = f"Generate a realistic image of a suspect with the following description: {request.description}"
    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }
    headers = {"Authorization": f"Bearer {GEMINI_API_KEY}", "Content-Type": "application/json"}
    response = requests.post(GEMINI_IMAGE_URL, json=payload, headers=headers)
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Gemini image API error.")
    data = response.json()
    # Extract image URL or base64 (depends on Gemini API response)
    image_url = data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "")
    return SuspectImageResponse(image_url=image_url)
