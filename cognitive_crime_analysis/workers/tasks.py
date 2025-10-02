# workers/tasks.py (Updated)
from celery import Celery
from neo4j import GraphDatabase
import spacy
from app.database import SessionLocal
from app.models import Case

celery_app = Celery('tasks', broker='redis://localhost:6379/0', backend='redis://localhost:6379/0')
nlp = spacy.load("en_core_web_sm")

NEO4J_URI = "bolt://localhost:7687"
NEO4J_AUTH = ("neo4j", "Crime2*graph")# Remember to set your password

def get_neo4j_driver():
    return GraphDatabase.driver(NEO4J_URI, auth=NEO4J_AUTH)

@celery_app.task
def process_case_file_task(case_id: int, file_content: str):
    print(f"WORKER: Starting NLP processing for case_id: {case_id}")
    doc = nlp(file_content)
    entities = []
    for ent in doc.ents:
        if ent.label_ in ["PERSON", "GPE", "LOC", "ORG", "DATE", "TIME"]:
            entities.append({"text": ent.text, "label": ent.label_})
    
    print(f"WORKER: Found {len(entities)} entities: {entities}")

    if entities:
        driver = get_neo4j_driver()
        with driver.session() as session:
            # Create a single Case node
            session.run("MERGE (c:Case {case_id: $case_id})", case_id=case_id)

            # For each entity, create the node and link it to the Case node
            for entity in entities:
                session.run("""
                    MERGE (c:Case {case_id: $case_id})
                    MERGE (e:Entity {name: $name, type: $type})
                    MERGE (e)-[:BELONGS_TO]->(c)
                """, case_id=case_id, name=entity['text'], type=entity['label'])
        driver.close()
        print(f"WORKER: Successfully wrote and linked {len(entities)} entities to Neo4j for case {case_id}.")
    
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
    return {"status": "Complete", "case_id": case_id, "entities_found": len(entities)}
