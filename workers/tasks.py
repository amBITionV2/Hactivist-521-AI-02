from celery import Celery
import spacy
import time

app = Celery ('tasks', broker='redis://redis:6379/0', backend='redis://redis:6379/0')
nlp = spacy.load("en_core_web_sm")

@app.task
def process_case_file(file_content: str, case_id: int):
    
    # 1. Perform NLP extraction on file_content
    doc = nlp(file_content)
    entities = [(ent.text, ent.label_) for ent in doc.ents]

    # 2. Connect to Neo4j (running in another container)
    # 3. Write entities to the graph
    # 4. Connect to PostgreSQL
    # 5. Update the status of 'case_id' to "Processed"
    print(f"WORKER: Starting processing for case_id: {case_id} (File: {filename})")
    return {"case_id": case_id, "status": "Success", "entities_found": len(entities)}