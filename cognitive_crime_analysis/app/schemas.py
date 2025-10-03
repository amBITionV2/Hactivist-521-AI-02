from pydantic import BaseModel
import datetime
from typing import Optional

# The shape of data when creating a new case
class CaseCreate(BaseModel):
    filename: str

# The shape of data when reading/returning a case from the API
class Case(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime.datetime
    file_path: Optional[str] = None
    image_analysis: Optional[str] = None
    suspect_image: Optional[str] = None

    class Config:
        # This allows the Pydantic model to read data from SQLAlchemy objects
        form_mode = True