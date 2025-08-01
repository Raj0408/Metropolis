from datetime import datetime
from typing import List,Dict,Any
from pydantic import BaseModel,Field,model_validator

class TaskDefinition(BaseModel):
    function: str
    dependencies: List[str] = Field(default_factory=list)

class PipelineBase(BaseModel):
    name:str = Field(...,min_length=3,max_length=100,description="The unique name of the pipeline.")
    definition: Dict[str,TaskDefinition]

class PipelineCreate(PipelineBase):
    pass

class PipelineGet(BaseModel):
    name:str

class Pipeline(PipelineBase):
    id:int
    created_at: datetime

    class Config:
        from_attributes = True

class PipelineRunBase(BaseModel):
    pipeline_id:int
    parameters:Dict[str,str]

class JobBase(BaseModel):
    task_id:str
    status:str

class Job(JobBase):
    id:int
    pipeline_run_id:int
    created_at:datetime

    class Config:
        from_attributes = True

class PipelineRunBase(BaseModel):
    pipeline_id:int
    status:str
    run_parameters:Dict[str,Any] = Field(default_factory=dict)

class PipelineRunCreate(BaseModel):
    run_parameters:Dict[str,Any] = Field(default_factory=True)

class PipelineRun(PipelineRunBase):
    id:int
    created_at:datetime
    jobs: List[Job] = []


    class Config:
        from_attributes = True


