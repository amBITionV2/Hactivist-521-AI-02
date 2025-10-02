from pydantic import BaseModel
import datetime

# The shape of data when creating a new case
class CaseCreate(BaseModel):
    filename: str

# The shape of data when reading/returning a case from the API
class Case(BaseModel):
    id: int
    filename: str
    status: str
    created_at: datetime.datetime

    class Config:
        # This allows the Pydantic model to read data from SQLAlchemy objects
        form_mode = True