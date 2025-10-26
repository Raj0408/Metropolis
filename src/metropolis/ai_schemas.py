from datetime import datetime
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator
from uuid import UUID
from enum import Enum

# Enums
class NodeType(str, Enum):
    AI_MODEL = "AI_MODEL"
    DATA_PROCESSOR = "DATA_PROCESSOR"
    TRANSFORMER = "TRANSFORMER"
    CONDITIONAL = "CONDITIONAL"
    MERGER = "MERGER"
    SPLITTER = "SPLITTER"
    CUSTOM = "CUSTOM"

class WorkflowStatus(str, Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"

class JobStatus(str, Enum):
    PENDING = "PENDING"
    QUEUED = "QUEUED"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    RETRYING = "RETRYING"

class PipelineRunStatus(str, Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
    PAUSED = "PAUSED"

# User Schemas
class UserBase(BaseModel):
    email: str = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")

class UserCreate(UserBase):
    password: str = Field(..., min_length=8, description="Password")

class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    password: Optional[str] = None

class User(UserBase):
    id: UUID
    is_active: bool
    is_admin: bool
    created_at: datetime
    last_login: Optional[datetime] = None

    class Config:
        from_attributes = True

# API Key Schemas
class APIKeyCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    expires_at: Optional[datetime] = None

class APIKey(APIKeyCreate):
    id: UUID
    user_id: UUID
    is_active: bool
    last_used: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True

# Workflow Node Schemas
class NodePosition(BaseModel):
    x: float = Field(..., description="X coordinate")
    y: float = Field(..., description="Y coordinate")

class NodeConnection(BaseModel):
    source_node: str = Field(..., description="Source node ID")
    target_node: str = Field(..., description="Target node ID")
    source_output: str = Field(..., description="Source output port")
    target_input: str = Field(..., description="Target input port")

class WorkflowNodeBase(BaseModel):
    node_id: str = Field(..., description="Unique node ID within workflow")
    name: str = Field(..., min_length=1, max_length=100)
    node_type: NodeType
    position: NodePosition
    config: Dict[str, Any] = Field(default_factory=dict)
    inputs: List[str] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)

class WorkflowNodeCreate(WorkflowNodeBase):
    pass

class WorkflowNode(WorkflowNodeBase):
    id: UUID
    workflow_id: UUID
    created_at: datetime

    class Config:
        from_attributes = True

# Workflow Schemas
class WorkflowBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    is_public: bool = False
    tags: List[str] = Field(default_factory=list)

class WorkflowCreate(WorkflowBase):
    definition: Dict[str, Any] = Field(default_factory=dict)
    nodes: List[WorkflowNodeCreate] = Field(default_factory=list)
    connections: List[NodeConnection] = Field(default_factory=list)

class WorkflowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_public: Optional[bool] = None
    tags: Optional[List[str]] = None
    definition: Optional[Dict[str, Any]] = None
    nodes: Optional[List[WorkflowNodeCreate]] = None
    connections: Optional[List[NodeConnection]] = None

class Workflow(WorkflowBase):
    id: UUID
    owner_id: UUID
    status: WorkflowStatus
    version: int
    created_at: datetime
    updated_at: Optional[datetime] = None
    nodes: List[WorkflowNode] = []

    class Config:
        from_attributes = True

# Workflow Run Schemas
class WorkflowRunCreate(BaseModel):
    parameters: Dict[str, Any] = Field(default_factory=dict)

class WorkflowRunUpdate(BaseModel):
    status: Optional[PipelineRunStatus] = None
    parameters: Optional[Dict[str, Any]] = None

class WorkflowRun(WorkflowRunCreate):
    id: UUID
    workflow_id: UUID
    status: PipelineRunStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    created_by: Optional[UUID] = None

    class Config:
        from_attributes = True

# Task Schemas
class TaskLogCreate(BaseModel):
    level: str = Field(..., description="Log level (INFO, WARNING, ERROR, DEBUG)")
    message: str = Field(..., description="Log message")
    log_metadata: Optional[Dict[str, Any]] = None

class TaskLog(TaskLogCreate):
    id: UUID
    task_id: UUID
    timestamp: datetime

    class Config:
        from_attributes = True

class WorkflowTaskBase(BaseModel):
    node_id: str
    task_id: str
    input_data: Optional[Dict[str, Any]] = None

class WorkflowTaskCreate(WorkflowTaskBase):
    pass

class WorkflowTaskUpdate(BaseModel):
    status: Optional[JobStatus] = None
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None

class WorkflowTask(WorkflowTaskBase):
    id: UUID
    workflow_run_id: UUID
    status: JobStatus
    output_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    logs: List[TaskLog] = []

    class Config:
        from_attributes = True

# AI Tool Schemas
class AIToolBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    category: str = Field(..., min_length=1, max_length=50)
    provider: str = Field(..., min_length=1, max_length=50)
    config_schema: Dict[str, Any] = Field(..., description="Configuration schema")
    input_schema: Dict[str, Any] = Field(..., description="Input data schema")
    output_schema: Dict[str, Any] = Field(..., description="Output data schema")

class AIToolCreate(AIToolBase):
    pass

class AIToolUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    provider: Optional[str] = None
    config_schema: Optional[Dict[str, Any]] = None
    input_schema: Optional[Dict[str, Any]] = None
    output_schema: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None

class AITool(AIToolBase):
    id: UUID
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True

# Real-time Status Schemas
class WorkflowRunStatus(BaseModel):
    run_id: UUID
    workflow_id: UUID
    status: PipelineRunStatus
    progress: float = Field(..., ge=0, le=100, description="Progress percentage")
    total_tasks: int
    completed_tasks: int
    failed_tasks: int
    running_tasks: int
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None

class TaskStatus(BaseModel):
    task_id: UUID
    node_id: str
    status: JobStatus
    progress: float = Field(..., ge=0, le=100)
    started_at: Optional[datetime] = None
    estimated_completion: Optional[datetime] = None
    error_message: Optional[str] = None

# Analytics Schemas
class WorkflowAnalytics(BaseModel):
    workflow_id: UUID
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration: Optional[float] = None
    success_rate: float = Field(..., ge=0, le=100)
    last_run: Optional[datetime] = None
    most_used_nodes: List[Dict[str, Any]] = Field(default_factory=list)

class SystemMetrics(BaseModel):
    active_workflows: int
    running_tasks: int
    queued_tasks: int
    failed_tasks: int
    system_load: float
    memory_usage: float
    cpu_usage: float
    timestamp: datetime

# Webhook Schemas
class WebhookEvent(BaseModel):
    event_type: str
    workflow_id: UUID
    run_id: Optional[UUID] = None
    task_id: Optional[UUID] = None
    status: str
    timestamp: datetime
    data: Dict[str, Any] = Field(default_factory=dict)

class WebhookConfig(BaseModel):
    url: str = Field(..., description="Webhook URL")
    events: List[str] = Field(..., description="Events to subscribe to")
    secret: Optional[str] = Field(None, description="Webhook secret for verification")
    is_active: bool = True
