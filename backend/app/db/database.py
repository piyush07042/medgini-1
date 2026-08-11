import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite DB File Path
DB_URL = "sqlite:///./medigenie_cdss.db"

engine = create_engine(
    DB_URL, 
    connect_args={"check_same_thread": False}  # Needed for SQLite in FastAPI
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """FastAPI Dependency for database session management."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()