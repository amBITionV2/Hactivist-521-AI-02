from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

## --- PostgreSQL Connection --- ##
## IMPORTANT: Replace 'YOUR_POSTGRES_PASSWORD' with the password you set during installation.
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:Rish2#san@localhost:5433/crime_db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()