from sqlalchemy import Column, Integer, String, DateTime,Text
from .database import Base
import datetime

class Case(Base):
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String, index=True)
    status = Column(String, default="pending")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    file_path = Column(String, nullable=True) # To store the path to the file
    image_analysis = Column(Text, nullable=True) # To store the AI's analysis of an image
    suspect_image = Column(Text, nullable=True)

