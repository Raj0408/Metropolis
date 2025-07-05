from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from . import models
from .database import engine, get_db
from .settings import settings

max_retries = 5
retry_delay = 5  # in seconds

for attempt in range(max_retries):
    try:
        models.Base.metadata.create_all(bind=engine)
        print("Database tables created successfully.")
        break  
    except Exception as e:
        print(f"Database connection failed (Attempt {attempt + 1}/{max_retries}): {e}")
        if attempt < max_retries - 1:
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)
        else:
            print("Could not connect to the database after several attempts. Exiting.")

app = FastAPI(title="Metropolis - Pipeline Orchestrator")

@app.get("/")
def read_root():
    return {"message": "Welcome to Metropolis API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    A health check endpoint that confirms API and Database connectivity.
    """
    try:
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "api_status": "ok",
        "database_status": db_status,
        "environment": settings.ENVIRONMENT
    }