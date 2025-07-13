from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import text
import time
from . import models
from .database import engine, get_db
from .settings import settings
from .schemas import PipelineCreate,Pipeline,PipelineGet,PipelineRunCreate
from .crud import get_pipeline_by_name,create_pipeline,get_pipeline_by_id,create_pipeline_run
from .validation import validate_pipeline_dag
from .broker import redis_client,READY_QUEUE_NAME
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
    db_pipeline = get_pipeline_by_name(db=db,name=pipeline_in.name)
    if db_pipeline:
        raise HTTPException(
            status_code=400, # Bad Request
            detail=f"Pipeline with name '{pipeline_in.name}' already exists"
        )
    try:
        validate_pipeline_dag(pipeline_in.definition)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return create_pipeline(db=db, pipeline=pipeline_in)
    
@app.get("/pipeline",response_model=Pipeline,status_code=201)
def get_pipeline(pipeline_name:PipelineGet,db:Session = Depends(get_db)):
    db_pipeline = get_pipeline_by_name(db=db,name=pipeline_name.name)
    print(db_pipeline.definition)
    if db_pipeline:
        return db_pipeline
    else:
        raise HTTPException(
            status_code=400, # Bad Request
            detail=f"Pipeline not Exists"
        )

@app.post("/pipelines/{pipeline_id}/run")
def trigger_pipeline_run(pipeline_id:int,run_in:PipelineRunCreate,db:Session = Depends(get_db)):

    pipeline = get_pipeline_by_id(db,pipeline_id)
    if not pipeline:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Pipeline with id {pipeline_id} not found."
        )
    pipeline_run = create_pipeline_run(db=db,pipeline=pipeline,run_in=run_in)


    root_jobs = []
    pipeline_def = pipeline.definition
    for job in  pipeline_run.jobs:
        if not pipeline_def[job.task_id]['dependencies']:
            root_jobs.append(job)

    
    for job in root_jobs:
        redis_client.rpush(READY_QUEUE_NAME,job.id)
        job.status = models.JobStatus.QUEUED
    

    pipeline_run.status = models.PipelineRunStatus.RUNNING

    db.commit()
    db.refresh(pipeline_run)

    return pipeline_run