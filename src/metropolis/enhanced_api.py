"""
Enhanced API for Metropolis AI Platform
Provides advanced features including real-time monitoring, webhooks, and comprehensive workflow management
"""

import asyncio
import json
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from fastapi import FastAPI, Depends, HTTPException, status, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc,text
import logging

from .database import get_db
from . import models, crud
from .models import User, Workflow, WorkflowRun, WorkflowTask, AITool, APIKey
from .ai_schemas import *
from .ai_workflow_engine import AIWorkflowEngine, ExecutionStrategy
from .advanced_monitoring import AdvancedMonitoring, AlertLevel
from .broker import redis_client

logger = logging.getLogger(__name__)

# Security
security = HTTPBearer()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
    
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    
    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)
    
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                # Remove dead connections
                self.active_connections.remove(connection)

manager = ConnectionManager()

# Enhanced FastAPI app
app = FastAPI(
    title="Metropolis AI Platform",
    description="Advanced AI workflow orchestration platform with real-time monitoring and analytics",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances
workflow_engine: Optional[AIWorkflowEngine] = None
monitoring: Optional[AdvancedMonitoring] = None

# Authentication
async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current user from API key"""
    if not credentials:
        raise HTTPException(status_code=401, detail="Authentication required")
    
    # Find API key
    api_key = db.query(models.APIKey).filter(models.APIKey.key_hash == credentials.credentials).first()
    if not api_key or not api_key.is_active:
        raise HTTPException(status_code=401, detail="Invalid API key")
    
    # Update last used
    api_key.last_used = datetime.utcnow()
    db.commit()
    
    # Get user
    user = db.query(models.User).filter(models.User.id == api_key.user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail="User not found or inactive")
    
    return user

# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    global workflow_engine, monitoring
    
    # Initialize workflow engine
    db = next(get_db())
    workflow_engine = AIWorkflowEngine(db, redis_client)
    monitoring = AdvancedMonitoring(db, redis_client)
    
    # Start monitoring
    asyncio.create_task(monitoring.start_monitoring())
    
    logger.info("Metropolis AI Platform started")

# Health check
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """Enhanced health check with system metrics"""
    try:
        # Database health
        db.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"
    
    # Redis health
    try:
        redis_client.ping()
        redis_status = "ok"
    except Exception as e:
        redis_status = f"error: {e}"
    
    # System metrics
    if monitoring:
        system_metrics = monitoring.get_system_metrics()
    else:
        system_metrics = None
    
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "database": db_status,
        "redis": redis_status,
        "system_metrics": system_metrics.__dict__ if system_metrics else None
    }

# User management
@app.post("/api/users", response_model=User, status_code=201)
async def create_user(user: UserCreate, db: Session = Depends(get_db)):
    """Create a new user"""
    # Check if user exists
    existing_user = db.query(models.User).filter(
        (models.User.email == user.email) | (models.User.username == user.username)
    ).first()
    
    if existing_user:
        raise HTTPException(status_code=400, detail="User already exists")
    
    # Create user (password should be hashed in production)
    db_user = models.User(
        id=str(uuid.uuid4()),
        email=user.email,
        username=user.username,
        hashed_password=user.password,  # Should hash in production
        is_active=True
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user

@app.post("/api/api-keys", response_model=APIKey, status_code=201)
async def create_api_key(
    api_key: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new API key"""
    # Generate API key
    key_value = f"mk_{uuid.uuid4().hex}"

    try:
        existing_user = db.query(models.User).filter(
            (models.User.username == api_key.name)
        ).first()
            
    except Exception as e:
        print(e)

    print(db_api_key)


    try:
        db_api_key = models.APIKey(
            id=str(uuid.uuid4()),
            user_id=existing_user.id,
            name=api_key.name,
            key_hash=key_value,  # Should hash in production
            is_active=True,
            expires_at=api_key.expires_at
        )
        
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        
        # Return the actual key value (only time it's shown)
        db_api_key.key_hash = key_value
        return db_api_key
    except Exception as e:
        print(e)
        return None

   

# Workflow management
@app.post("/api/workflows", response_model=Workflow, status_code=201)
async def create_workflow(
    workflow: WorkflowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new workflow"""
    db_workflow = models.Workflow(
        id=str(uuid.uuid4()),
        name=workflow.name,
        description=workflow.description,
        owner_id=current_user.id,
        status=models.WorkflowStatus.DRAFT,
        definition=workflow.definition,
        is_public=workflow.is_public,
        tags=workflow.tags
    )
    
    db.add(db_workflow)
    db.commit()
    db.refresh(db_workflow)
    
    # Create workflow nodes
    for node_data in workflow.nodes:
        db_node = models.WorkflowNode(
            id=str(uuid.uuid4()),
            workflow_id=db_workflow.id,
            node_id=node_data.node_id,
            name=node_data.name,
            node_type=node_data.node_type,
            position_x=node_data.position.x,
            position_y=node_data.position.y,
            config=node_data.config,
            inputs=node_data.inputs,
            outputs=node_data.outputs
        )
        db.add(db_node)
    
    db.commit()
    return db_workflow

@app.get("/api/workflows", response_model=List[Workflow])
async def list_workflows(
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List workflows for the current user"""
    workflows = db.query(models.Workflow).filter(
        (models.Workflow.owner_id == current_user.id) | (models.Workflow.is_public == True)
    ).offset(skip).limit(limit).all()
    
    return workflows

@app.get("/api/workflows/{workflow_id}", response_model=Workflow)
async def get_workflow(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific workflow"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    return workflow

@app.post("/api/workflows/{workflow_id}/run", response_model=WorkflowRun, status_code=201)
async def run_workflow(
    workflow_id: str,
    run_data: WorkflowRunCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Run a workflow"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Create workflow run
    workflow_run = models.WorkflowRun(
        id=str(uuid.uuid4()),
        workflow_id=workflow_id,
        status=models.PipelineRunStatus.PENDING,
        parameters=run_data.parameters,
        created_by=current_user.id,
        created_at=datetime.utcnow()
    )
    
    db.add(workflow_run)
    db.commit()
    db.refresh(workflow_run)
    
    # Execute workflow in background
    if workflow_engine:
        background_tasks.add_task(
            workflow_engine.execute_workflow,
            workflow_id,
            run_data.parameters,
            ExecutionStrategy.OPTIMIZED
        )
    
    return workflow_run

@app.get("/api/workflows/{workflow_id}/runs", response_model=List[WorkflowRun])
async def list_workflow_runs(
    workflow_id: str,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List runs for a workflow"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    runs = db.query(models.WorkflowRun).filter(
        models.WorkflowRun.workflow_id == workflow_id
    ).order_by(desc(models.WorkflowRun.created_at)).offset(skip).limit(limit).all()
    
    return runs

@app.get("/api/workflows/{workflow_id}/runs/{run_id}/status")
async def get_workflow_run_status(
    workflow_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get real-time status of a workflow run"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if workflow_engine:
        status = workflow_engine.get_workflow_status(run_id)
        return status
    else:
        raise HTTPException(status_code=500, detail="Workflow engine not available")

# Real-time WebSocket endpoint
@app.websocket("/ws/{workflow_id}")
async def websocket_endpoint(websocket: WebSocket, workflow_id: str):
    """WebSocket endpoint for real-time updates"""
    await manager.connect(websocket)
    
    try:
        while True:
            # Send periodic updates
            if workflow_engine:
                status = workflow_engine.get_workflow_status(workflow_id)
                await manager.send_personal_message(
                    json.dumps(status.__dict__, default=str),
                    websocket
                )
            
            await asyncio.sleep(5)  # Update every 5 seconds
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)

# Streaming endpoint for real-time logs
@app.get("/api/workflows/{workflow_id}/runs/{run_id}/logs")
async def stream_workflow_logs(
    workflow_id: str,
    run_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Stream real-time logs for a workflow run"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    async def generate_logs():
        while True:
            # Get latest logs
            logs = db.query(models.TaskLog).join(models.WorkflowTask).filter(
                models.WorkflowTask.workflow_run_id == run_id
            ).order_by(desc(models.TaskLog.timestamp)).limit(10).all()
            
            yield f"data: {json.dumps([log.__dict__ for log in logs], default=str)}\n\n"
            await asyncio.sleep(2)
    
    return StreamingResponse(generate_logs(), media_type="text/plain")

# Analytics endpoints
@app.get("/api/analytics/workflows/{workflow_id}")
async def get_workflow_analytics(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get analytics for a workflow"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if monitoring:
        analytics = monitoring.get_workflow_analytics(workflow_id)
        return analytics
    else:
        raise HTTPException(status_code=500, detail="Monitoring not available")

@app.get("/api/analytics/system")
async def get_system_analytics(
    current_user: User = Depends(get_current_user)
):
    """Get system-wide analytics"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if monitoring:
        metrics = monitoring.get_system_metrics()
        return metrics
    else:
        raise HTTPException(status_code=500, detail="Monitoring not available")

# AI Tools marketplace
@app.get("/api/ai-tools", response_model=List[AITool])
async def list_ai_tools(
    category: Optional[str] = None,
    provider: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List available AI tools"""
    query = db.query(models.AITool).filter(models.AITool.is_active == True)
    
    if category:
        query = query.filter(models.AITool.category == category)
    
    if provider:
        query = query.filter(models.AITool.provider == provider)
    
    tools = query.offset(skip).limit(limit).all()
    return tools

@app.post("/api/ai-tools", response_model=AITool, status_code=201)
async def create_ai_tool(
    tool: AIToolCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new AI tool"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    db_tool = models.AITool(
        id=str(uuid.uuid4()),
        name=tool.name,
        description=tool.description,
        category=tool.category,
        provider=tool.provider,
        config_schema=tool.config_schema,
        input_schema=tool.input_schema,
        output_schema=tool.output_schema,
        is_active=True
    )
    
    db.add(db_tool)
    db.commit()
    db.refresh(db_tool)
    
    return db_tool

# Monitoring endpoints
@app.get("/api/monitoring/alerts")
async def get_alerts(
    level: Optional[AlertLevel] = None,
    limit: int = 50,
    current_user: User = Depends(get_current_user)
):
    """Get system alerts"""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if monitoring:
        alerts = monitoring.get_recent_alerts(limit)
        if level:
            alerts = [alert for alert in alerts if alert.level == level]
        return alerts
    else:
        raise HTTPException(status_code=500, detail="Monitoring not available")

# Webhook endpoints
@app.post("/api/webhooks")
async def create_webhook(
    webhook: WebhookConfig,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a webhook configuration"""
    # Store webhook config in database or Redis
    webhook_id = str(uuid.uuid4())
    
    # Store in Redis for now
    redis_client.hset(
        f"metropolis:webhooks:{webhook_id}",
        mapping={
            "user_id": str(current_user.id),
            "url": webhook.url,
            "events": json.dumps(webhook.events),
            "secret": webhook.secret or "",
            "is_active": str(webhook.is_active)
        }
    )
    
    return {"webhook_id": webhook_id, "status": "created"}

# Export endpoints
@app.get("/api/workflows/{workflow_id}/export")
async def export_workflow(
    workflow_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Export a workflow in various formats"""
    workflow = db.query(models.Workflow).filter(models.Workflow.id == workflow_id).first()
    
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Check permissions
    if workflow.owner_id != current_user.id and not workflow.is_public:
        raise HTTPException(status_code=403, detail="Access denied")
    
    if format == "json":
        return {
            "workflow": workflow.__dict__,
            "nodes": [node.__dict__ for node in workflow.nodes]
        }
    elif format == "yaml":
        import yaml
        return yaml.dump({
            "workflow": workflow.__dict__,
            "nodes": [node.__dict__ for node in workflow.nodes]
        })
    else:
        raise HTTPException(status_code=400, detail="Unsupported format")

# Import endpoints
@app.post("/api/workflows/import")
async def import_workflow(
    workflow_data: Dict[str, Any],
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Import a workflow"""
    # Implementation for importing workflows
    # This would parse the workflow data and create the workflow
    pass
