# app/main.py
from fastapi import FastAPI

app = FastAPI(title="Cognitive Crime Analysis System API")

@app.get("/")
def read_root():
    return {"status": "API is running"}

# We will add endpoints like /cases, /analysis, etc. here