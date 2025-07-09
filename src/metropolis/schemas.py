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

class Pipeline(PipelineBase):
    id:int
    created_at: datetime

    class Config:
        from_attributes = True
    


