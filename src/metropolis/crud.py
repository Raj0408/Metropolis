from sqlalchemy.orm import Session
from . import models,schemas

def get_pipeline_by_name(db:Session,name:str) -> models.Pipeline | None:

    return db.query(models.Pipeline).filter(models.Pipeline.name == name).first()

def create_pipeline(db:Session,pipeline:schemas.PipelineCreate) -> models.Pipeline:

    """
    Create the pipeline and store into the database

    """ 
    db_pipeline = models.Pipeline(
        name = pipeline.name,
        definition = pipeline.model_dump()['definition']
    )
    db.add(db_pipeline)
    db.commit()
    db.refresh(db_pipeline)
    return db_pipeline


def get_pipeline_by_id(db:Session,id:int):
    return db.query(models.Pipeline).filter(models.Pipeline.id == id).first()

def get_pipeline_run(db:Session,id:int):
    pipeline_run = db.query(models.PipelineRun).filter(models.PipelineRun.pipeline_id == id).all()
    return pipeline_run


def create_pipeline_run(db:Session,pipeline:models.Pipeline,run_in:schemas.PipelineRunCreate) -> models.PipelineRun:
    
    db_pipeline_run = models.PipelineRun(
        pipeline_id = pipeline.id,
        parameters =run_in.run_parameters,
        status = models.PipelineRunStatus.PENDING
    )
    db.add(db_pipeline_run)
    db.commit()
    db.refresh(db_pipeline_run)


    jobs = []

    for task_name in pipeline.definition:
        job = models.Job(
            task_id=task_name,
            pipeline_run_id = db_pipeline_run.id,
            status = models.JobStatus.PENDING
        )
        jobs.append(job)
    
    db.add_all(jobs)
    db.commit()
    db.refresh(db_pipeline_run)

    return db_pipeline_run

   
