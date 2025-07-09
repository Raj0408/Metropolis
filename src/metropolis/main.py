from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from . import models
from .database import engine, get_db
from .settings import settings
from .schemas import PipelineCreate,Pipeline
from .crud import get_pipeline_by_name,create_pipeline

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

@app.post("/pipelines",response_model=Pipeline,status_code=201)
def handle_pipeline_create(pipeline_in:PipelineCreate,db:Session = Depends(get_db)):
    db_pipeline = get_pipeline_by_name(name=pipeline_in.name)
    if db_pipeline:
        raise HTTPException(
            status_code=400, # Bad Request
            detail=f"Pipeline with name '{pipeline_in.name}' already exists"
        )
    try:
        return create_pipeline(pipeline=pipeline_in,db=db)
    except Exception as e:
        raise HTTPException(status_code=500,detail=str(e))
    
