from datetime import datetime
from typing import List,Dict,Any
from pydantic import BaseModel,Field,model_validator

class TaskDefinition():
    function: str
    dependencies: List[str] = Field(default_factory=list)
    pass

class PipelineBase():
    name:str = Field(...,min_length=3,max_length=100,description="The unique name of the pipeline.")
    definition: Dict[str,TaskDefinition]

    pass

class PipelineCreate(PipelineBase):
    pass

class Pipeline(PipelineBase):
    id:int
    created_at = datetime

    class Config:
        from_attributes = True
    pass


