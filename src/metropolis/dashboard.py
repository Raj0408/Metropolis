"""
Modern Web Dashboard for Metropolis AI Platform
Provides a beautiful, responsive interface for workflow management and monitoring
"""

from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from typing import Dict, List, Any
import json
import logging

from .database import get_db
from .models import User, Workflow, WorkflowRun, WorkflowTask
from .ai_schemas import SystemMetrics, WorkflowAnalytics
from .advanced_monitoring import AdvancedMonitoring

logger = logging.getLogger(__name__)

# Create dashboard app
dashboard_app = FastAPI(
    title="Metropolis Dashboard",
    description="Web dashboard for Metropolis AI Platform"
)

# Templates
templates = Jinja2Templates(directory="templates")

# Static files
dashboard_app.mount("/static", StaticFiles(directory="static"), name="static")

# Dashboard routes
@dashboard_app.get("/", response_class=HTMLResponse)
async def dashboard_home(request: Request):
    """Main dashboard page"""
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "title": "Metropolis AI Platform Dashboard"
    })

@dashboard_app.get("/workflows", response_class=HTMLResponse)
async def workflows_page(request: Request):
    """Workflows management page"""
    return templates.TemplateResponse("workflows.html", {
        "request": request,
        "title": "Workflows - Metropolis AI Platform"
    })

@dashboard_app.get("/workflows/{workflow_id}", response_class=HTMLResponse)
async def workflow_detail(request: Request, workflow_id: str):
    """Workflow detail page"""
    return templates.TemplateResponse("workflow_detail.html", {
        "request": request,
        "workflow_id": workflow_id,
        "title": f"Workflow {workflow_id} - Metropolis AI Platform"
    })

@dashboard_app.get("/monitoring", response_class=HTMLResponse)
async def monitoring_page(request: Request):
    """Monitoring dashboard page"""
    return templates.TemplateResponse("monitoring.html", {
        "request": request,
        "title": "Monitoring - Metropolis AI Platform"
    })

@dashboard_app.get("/analytics", response_class=HTMLResponse)
async def analytics_page(request: Request):
    """Analytics page"""
    return templates.TemplateResponse("analytics.html", {
        "request": request,
        "title": "Analytics - Metropolis AI Platform"
    })

# API endpoints for dashboard
@dashboard_app.get("/api/dashboard/overview")
async def dashboard_overview(db: Session = Depends(get_db)):
    """Get dashboard overview data"""
    # Get system metrics
    monitoring = AdvancedMonitoring(db, None)  # Redis client not needed for basic queries
    system_metrics = monitoring.get_system_metrics()
    
    # Get workflow statistics
    total_workflows = db.query(Workflow).count()
    active_workflows = db.query(WorkflowRun).filter(
        WorkflowRun.status == "RUNNING"
    ).count()
    
    # Get recent activity
    recent_runs = db.query(WorkflowRun).order_by(
        WorkflowRun.created_at.desc()
    ).limit(10).all()
    
    return {
        "system_metrics": system_metrics.__dict__,
        "total_workflows": total_workflows,
        "active_workflows": active_workflows,
        "recent_runs": [
            {
                "id": str(run.id),
                "workflow_id": str(run.workflow_id),
                "status": run.status,
                "created_at": run.created_at.isoformat()
            }
            for run in recent_runs
        ]
    }

@dashboard_app.get("/api/dashboard/workflows")
async def dashboard_workflows(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get workflows for dashboard"""
    workflows = db.query(Workflow).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(workflow.id),
            "name": workflow.name,
            "description": workflow.description,
            "status": workflow.status,
            "is_public": workflow.is_public,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat() if workflow.updated_at else None
        }
        for workflow in workflows
    ]

@dashboard_app.get("/api/dashboard/workflows/{workflow_id}/runs")
async def dashboard_workflow_runs(
    workflow_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """Get workflow runs for dashboard"""
    runs = db.query(WorkflowRun).filter(
        WorkflowRun.workflow_id == workflow_id
    ).order_by(WorkflowRun.created_at.desc()).offset(skip).limit(limit).all()
    
    return [
        {
            "id": str(run.id),
            "status": run.status,
            "created_at": run.created_at.isoformat(),
            "started_at": run.started_at.isoformat() if run.started_at else None,
            "completed_at": run.completed_at.isoformat() if run.completed_at else None
        }
        for run in runs
    ]

@dashboard_app.get("/api/dashboard/monitoring/metrics")
async def monitoring_metrics(db: Session = Depends(get_db)):
    """Get monitoring metrics"""
    monitoring = AdvancedMonitoring(db, None)
    
    # Get system metrics
    system_metrics = monitoring.get_system_metrics()
    
    # Get recent alerts
    alerts = monitoring.get_recent_alerts(limit=20)
    
    return {
        "system_metrics": system_metrics.__dict__,
        "alerts": [
            {
                "id": alert.id,
                "level": alert.level,
                "title": alert.title,
                "message": alert.message,
                "timestamp": alert.timestamp.isoformat(),
                "workflow_id": alert.workflow_id,
                "task_id": alert.task_id
            }
            for alert in alerts
        ]
    }
