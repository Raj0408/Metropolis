from sqlalchemy.orm import Session
from . import models, schemas, ai_schemas
from typing import List, Optional
import uuid

# Legacy Pipeline functions (for backward compatibility)
def get_pipeline_by_name(db: Session, name: str) -> models.Pipeline | None:
    return db.query(models.Pipeline).filter(models.Pipeline.name == name).first()

def create_pipeline(db: Session, pipeline: schemas.PipelineCreate) -> models.Pipeline:
    """
    Create the pipeline and store into the database
    """ 
    db_pipeline = models.Pipeline(
        name=pipeline.name,
        definition=pipeline.model_dump()['definition']
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline

def get_pipeline_by_id(db: Session, id: int):
    return db.query(models.Pipeline).filter(models.Pipeline.id == id).first()

# New AI Workflow functions
def create_user(db: Session, user: ai_schemas.UserCreate) -> models.User:
    """Create a new user"""
    db_user = models.User(
        email=user.email,
        username=user.username,
        hashed_password=user.password,  # In production, hash this
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def get_user_by_email(db: Session, email: str) -> Optional[models.User]:
    """Get user by email"""
    return db.query(models.User).filter(models.User.email == email).first()

def create_workflow(db: Session, workflow: ai_schemas.WorkflowCreate, owner_id: str) -> models.Workflow:
    """Create a new workflow"""
    db_workflow = models.Workflow(
        id=str(uuid.uuid4()),
        name=workflow.name,
        description=workflow.description,
        owner_id=owner_id,
        status=models.WorkflowStatus.DRAFT,
        definition=workflow.definition,
        is_public=workflow.is_public,
        tags=workflow.tags
    )
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    return db_workflow

def get_workflow_by_id(db: Session, workflow_id: str) -> Optional[models.Workflow]:
    """Get workflow by ID"""
    return db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()

def create_workflow_run(db: Session, workflow_id: str, run_data: ai_schemas.WorkflowRunCreate, created_by: str) -> models.WorkflowRun:
    """Create a new workflow run"""
    db_workflow_run = models.WorkflowRun(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        status=models.PipelineRunStatus.PENDING,
        parameters=run_data.parameters,
        created_by=created_by
    )
    db.add(db_workflow_run)
    db.commit()
    db.refresh(db_workflow_run)
    return db_workflow_run

def get_workflow_run_by_id(db: Session, run_id: str) -> Optional[models.WorkflowRun]:
    """Get workflow run by ID"""
    return db.query(models.WorkflowRun).filter(models.WorkflowRun.id == run_id).first()

def create_workflow_task(db: Session, task_data: ai_schemas.WorkflowTaskCreate, workflow_run_id: str) -> models.WorkflowTask:
    """Create a new workflow task"""
    db_task = models.WorkflowTask(
        id=str(uuid.uuid4()),
        workflow_run_id=workflow_run_id,
        node_id=task_data.node_id,
        task_id=task_data.task_id,
        input_data=task_data.input_data,
        status=models.JobStatus.PENDING
    )
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

def get_workflow_tasks_by_run_id(db: Session, run_id: str) -> List[models.WorkflowTask]:
    """Get all tasks for a workflow run"""
    return db.query(models.WorkflowTask).filter(models.WorkflowTask.workflow_run_id == run_id).all()

def update_task_status(db: Session, task_id: str, status: models.JobStatus, output_data: dict = None, error_message: str = None):
    """Update task status"""
    task = db.query(models.WorkflowTask).filter(models.WorkflowTask.id == task_id).first()
    if task:
        task.status = status
        if output_data:
            task.output_data = output_data
        if error_message:
            task.error_message = error_message
        db.commit()
        db.refresh(task)
    return task

def create_task_log(db: Session, task_id: str, level: str, message: str, log_metadata: dict = None) -> models.TaskLog:
    """Create a task log entry"""
    db_log = models.TaskLog(
        id=str(uuid.uuid4()),
        task_id=task_id,
        level=level,
        message=message,
        log_metadata=log_metadata
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

# Legacy function for backward compatibility (returns empty list)
def get_pipeline_run(db: Session, id: int):
    """Legacy function - returns empty list since PipelineRun was removed"""
    return []