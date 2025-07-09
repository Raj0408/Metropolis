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
