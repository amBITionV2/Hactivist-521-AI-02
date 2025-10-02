from fastapi import APIRouter, UploadFile, File
from workers.tasks import process_case_file

router = APIRouter()

# Dummy function for DB insert, replace with actual implementation
def create_case_in_db(filename: str) -> int:
    # TODO: Save metadata to PostgreSQL and return case_id
    return 1  # Replace with actual case_id from DB

@router.post("/cases/upload")
async def upload_case(file: UploadFile = File(...)):
    # 1. Save the case metadata to PostgreSQL, get back a case_id
    case_id = create_case_in_db(file.filename)

    # 2. Get file content
    content = await file.read()

    # 3. Dispatch the background task
    process_case_file.delay(content.decode('utf-8'), case_id)

    return {"message": "Case file received and is being processed.", "case_id": case_id}
