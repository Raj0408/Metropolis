"""
Advanced Monitoring and Analytics System for Metropolis
Provides real-time monitoring, alerting, and performance analytics
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import psutil
import numpy as np
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, and_
from redis import Redis

from .models import (
    Workflow, WorkflowRun, WorkflowTask, TaskLog,
    JobStatus, PipelineRunStatus, NodeType
)
from .ai_schemas import SystemMetrics, WorkflowAnalytics, WebhookEvent

logger = logging.getLogger(__name__)

class AlertLevel(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class MetricType(str, Enum):
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    SUMMARY = "summary"

@dataclass
class Alert:
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    metadata: Dict[str, Any] = None

@dataclass
class Metric:
    name: str
    value: float
    metric_type: MetricType
    labels: Dict[str, str]
    timestamp: datetime

class AdvancedMonitoring:
    """
    Advanced monitoring system with real-time metrics, alerting, and analytics
    """
    
    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis = redis_client
        self.metrics_buffer: List[Metric] = []
        self.alerts: List[Alert] = []
        self.alert_handlers: Dict[AlertLevel, List[Callable]] = {
            AlertLevel.INFO: [],
            AlertLevel.WARNING: [],
            AlertLevel.ERROR: [],
            AlertLevel.CRITICAL: []
        }
        self.monitoring_active = False
        self.metrics_interval = 10  # seconds
        self.alert_check_interval = 30  # seconds
        
    async def start_monitoring(self):
        """Start the monitoring system"""
        self.monitoring_active = True
        
        # Start monitoring tasks
        tasks = [
            asyncio.create_task(self._collect_system_metrics()),
            asyncio.create_task(self._collect_workflow_metrics()),
            asyncio.create_task(self._check_alerts()),
            asyncio.create_task(self._flush_metrics()),
        ]
        
        await asyncio.gather(*tasks)
    
    def stop_monitoring(self):
        """Stop the monitoring system"""
        self.monitoring_active = False
    
    async def _collect_system_metrics(self):
        """Collect system-level metrics"""
        while self.monitoring_active:
            try:
                # CPU metrics
                cpu_percent = psutil.cpu_percent(interval=1)
                cpu_count = psutil.cpu_count()
                
                # Memory metrics
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                memory_used = memory.used / (1024**3)  # GB
                memory_total = memory.total / (1024**3)  # GB
                
                # Disk metrics
                disk = psutil.disk_usage('/')
                disk_percent = (disk.used / disk.total) * 100
                disk_used = disk.used / (1024**3)  # GB
                disk_total = disk.total / (1024**3)  # GB
                
                # Network metrics
                network = psutil.net_io_counters()
                network_bytes_sent = network.bytes_sent
                network_bytes_recv = network.bytes_recv
                
                # Record metrics
                self._record_metric("system_cpu_percent", cpu_percent, MetricType.GAUGE)
                self._record_metric("system_cpu_count", cpu_count, MetricType.GAUGE)
                self._record_metric("system_memory_percent", memory_percent, MetricType.GAUGE)
                self._record_metric("system_memory_used_gb", memory_used, MetricType.GAUGE)
                self._record_metric("system_memory_total_gb", memory_total, MetricType.GAUGE)
                self._record_metric("system_disk_percent", disk_percent, MetricType.GAUGE)
                self._record_metric("system_disk_used_gb", disk_used, MetricType.GAUGE)
                self._record_metric("system_disk_total_gb", disk_total, MetricType.GAUGE)
                self._record_metric("system_network_bytes_sent", network_bytes_sent, MetricType.COUNTER)
                self._record_metric("system_network_bytes_recv", network_bytes_recv, MetricType.COUNTER)
                
                # Check for system alerts
                await self._check_system_alerts(cpu_percent, memory_percent, disk_percent)
                
            except Exception as e:
                logger.error(f"Error collecting system metrics: {e}")
            
            await asyncio.sleep(self.metrics_interval)
    
    async def _collect_workflow_metrics(self):
        """Collect workflow-specific metrics"""
        while self.monitoring_active:
            try:
                # Active workflows
                active_workflows = self.db.query(WorkflowRun).filter(
                    WorkflowRun.status == PipelineRunStatus.RUNNING
                ).count()
                
                # Task metrics
                total_tasks = self.db.query(WorkflowTask).count()
                running_tasks = self.db.query(WorkflowTask).filter(
                    WorkflowTask.status == JobStatus.RUNNING
                ).count()
                queued_tasks = self.db.query(WorkflowTask).filter(
                    WorkflowTask.status == JobStatus.QUEUED
                ).count()
                failed_tasks = self.db.query(WorkflowTask).filter(
                    WorkflowTask.status == JobStatus.FAILED
                ).count()
                successful_tasks = self.db.query(WorkflowTask).filter(
                    WorkflowTask.status == JobStatus.SUCCESS
                ).count()
                
                # Success rate
                success_rate = (successful_tasks / total_tasks * 100) if total_tasks > 0 else 0
                
                # Average task duration
                completed_tasks = self.db.query(WorkflowTask).filter(
                    and_(
                        WorkflowTask.status == JobStatus.SUCCESS,
                        WorkflowTask.started_at.isnot(None),
                        WorkflowTask.completed_at.isnot(None)
                    )
                ).all()
                
                if completed_tasks:
                    durations = []
                    for task in completed_tasks:
                        duration = (task.completed_at - task.started_at).total_seconds()
                        durations.append(duration)
                    
                    avg_duration = np.mean(durations)
                    median_duration = np.median(durations)
                    p95_duration = np.percentile(durations, 95)
                else:
                    avg_duration = 0
                    median_duration = 0
                    p95_duration = 0
                
                # Record metrics
                self._record_metric("workflows_active", active_workflows, MetricType.GAUGE)
                self._record_metric("tasks_total", total_tasks, MetricType.COUNTER)
                self._record_metric("tasks_running", running_tasks, MetricType.GAUGE)
                self._record_metric("tasks_queued", queued_tasks, MetricType.GAUGE)
                self._record_metric("tasks_failed", failed_tasks, MetricType.COUNTER)
                self._record_metric("tasks_successful", successful_tasks, MetricType.COUNTER)
                self._record_metric("tasks_success_rate", success_rate, MetricType.GAUGE)
                self._record_metric("tasks_avg_duration", avg_duration, MetricType.HISTOGRAM)
                self._record_metric("tasks_median_duration", median_duration, MetricType.HISTOGRAM)
                self._record_metric("tasks_p95_duration", p95_duration, MetricType.HISTOGRAM)
                
                # Check for workflow alerts
                await self._check_workflow_alerts(active_workflows, failed_tasks, success_rate)
                
            except Exception as e:
                logger.error(f"Error collecting workflow metrics: {e}")
            
            await asyncio.sleep(self.metrics_interval)
    
    async def _check_system_alerts(self, cpu_percent: float, memory_percent: float, disk_percent: float):
        """Check for system-level alerts"""
        # CPU alert
        if cpu_percent > 90:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "High CPU Usage",
                f"CPU usage is {cpu_percent:.1f}%",
                metadata={"cpu_percent": cpu_percent}
            )
        elif cpu_percent > 80:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated CPU Usage",
                f"CPU usage is {cpu_percent:.1f}%",
                metadata={"cpu_percent": cpu_percent}
            )
        
        # Memory alert
        if memory_percent > 95:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "High Memory Usage",
                f"Memory usage is {memory_percent:.1f}%",
                metadata={"memory_percent": memory_percent}
            )
        elif memory_percent > 85:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated Memory Usage",
                f"Memory usage is {memory_percent:.1f}%",
                metadata={"memory_percent": memory_percent}
            )
        
        # Disk alert
        if disk_percent > 95:
            await self._create_alert(
                AlertLevel.CRITICAL,
                "High Disk Usage",
                f"Disk usage is {disk_percent:.1f}%",
                metadata={"disk_percent": disk_percent}
            )
        elif disk_percent > 85:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated Disk Usage",
                f"Disk usage is {disk_percent:.1f}%",
                metadata={"disk_percent": disk_percent}
            )
    
    async def _check_workflow_alerts(self, active_workflows: int, failed_tasks: int, success_rate: float):
        """Check for workflow-level alerts"""
        # Too many active workflows
        if active_workflows > 100:
            await self._create_alert(
                AlertLevel.WARNING,
                "High Workflow Load",
                f"{active_workflows} workflows are currently active",
                metadata={"active_workflows": active_workflows}
            )
        
        # High failure rate
        if success_rate < 80 and failed_tasks > 10:
            await self._create_alert(
                AlertLevel.ERROR,
                "High Task Failure Rate",
                f"Success rate is {success_rate:.1f}% with {failed_tasks} failed tasks",
                metadata={"success_rate": success_rate, "failed_tasks": failed_tasks}
            )
        elif success_rate < 90:
            await self._create_alert(
                AlertLevel.WARNING,
                "Elevated Task Failure Rate",
                f"Success rate is {success_rate:.1f}%",
                metadata={"success_rate": success_rate}
            )
    
    async def _check_alerts(self):
        """Check for various alert conditions"""
        while self.monitoring_active:
            try:
                # Check for stuck tasks
                stuck_tasks = self.db.query(WorkflowTask).filter(
                    and_(
                        WorkflowTask.status == JobStatus.RUNNING,
                        WorkflowTask.started_at < datetime.utcnow() - timedelta(hours=1)
                    )
                ).all()
                
                for task in stuck_tasks:
                    await self._create_alert(
                        AlertLevel.ERROR,
                        "Stuck Task",
                        f"Task {task.task_id} has been running for over 1 hour",
                        task_id=task.id,
                        workflow_id=task.workflow_run_id
                    )
                
                # Check for failed workflows
                failed_workflows = self.db.query(WorkflowRun).filter(
                    and_(
                        WorkflowRun.status == PipelineRunStatus.FAILED,
                        WorkflowRun.created_at > datetime.utcnow() - timedelta(hours=1)
                    )
                ).all()
                
                for workflow in failed_workflows:
                    await self._create_alert(
                        AlertLevel.ERROR,
                        "Failed Workflow",
                        f"Workflow {workflow.id} has failed",
                        workflow_id=workflow.id
                    )
                
            except Exception as e:
                logger.error(f"Error checking alerts: {e}")
            
            await asyncio.sleep(self.alert_check_interval)
    
    async def _create_alert(
        self, 
        level: AlertLevel, 
        title: str, 
        message: str,
        workflow_id: Optional[str] = None,
        task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Create a new alert"""
        alert = Alert(
            id=f"alert_{int(time.time())}_{len(self.alerts)}",
            level=level,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            workflow_id=workflow_id,
            task_id=task_id,
            metadata=metadata or {}
        )
        
        self.alerts.append(alert)
        
        # Store in Redis for persistence
        self.redis.lpush("metropolis:alerts", json.dumps(asdict(alert), default=str))
        
        # Trigger alert handlers
        handlers = self.alert_handlers.get(level, [])
        for handler in handlers:
            try:
                await handler(alert)
            except Exception as e:
                logger.error(f"Error in alert handler: {e}")
        
        logger.info(f"Alert created: {level.value} - {title}")
    
    def _record_metric(self, name: str, value: float, metric_type: MetricType, labels: Dict[str, str] = None):
        """Record a metric"""
        metric = Metric(
            name=name,
            value=value,
            metric_type=metric_type,
            labels=labels or {},
            timestamp=datetime.utcnow()
        )
        
        self.metrics_buffer.append(metric)
        
        # Store in Redis for real-time access
        metric_key = f"metropolis:metrics:{name}"
        self.redis.lpush(metric_key, json.dumps({
            "value": value,
            "timestamp": metric.timestamp.isoformat(),
            "labels": labels or {}
        }))
        
        # Keep only last 1000 metrics per type
        self.redis.ltrim(metric_key, 0, 999)
    
    async def _flush_metrics(self):
        """Flush metrics to persistent storage"""
        while self.monitoring_active:
            try:
                if self.metrics_buffer:
                    # Store metrics in database or external system
                    # For now, just clear the buffer
                    self.metrics_buffer.clear()
                
            except Exception as e:
                logger.error(f"Error flushing metrics: {e}")
            
            await asyncio.sleep(60)  # Flush every minute
    
    def add_alert_handler(self, level: AlertLevel, handler: Callable):
        """Add an alert handler for a specific level"""
        self.alert_handlers[level].append(handler)
    
    def get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # Get latest metrics from Redis
        cpu_metric = self.redis.lindex("metropolis:metrics:system_cpu_percent", 0)
        memory_metric = self.redis.lindex("metropolis:metrics:system_memory_percent", 0)
        
        cpu_usage = 0.0
        memory_usage = 0.0
        
        if cpu_metric:
            cpu_data = json.loads(cpu_metric)
            cpu_usage = cpu_data["value"]
        
        if memory_metric:
            memory_data = json.loads(memory_metric)
            memory_usage = memory_data["value"]
        
        # Get workflow metrics
        active_workflows = self.db.query(WorkflowRun).filter(
            WorkflowRun.status == PipelineRunStatus.RUNNING
        ).count()
        
        running_tasks = self.db.query(WorkflowTask).filter(
            WorkflowTask.status == JobStatus.RUNNING
        ).count()
        
        queued_tasks = self.db.query(WorkflowTask).filter(
            WorkflowTask.status == JobStatus.QUEUED
        ).count()
        
        failed_tasks = self.db.query(WorkflowTask).filter(
            WorkflowTask.status == JobStatus.FAILED
        ).count()
        
        return SystemMetrics(
            active_workflows=active_workflows,
            running_tasks=running_tasks,
            queued_tasks=queued_tasks,
            failed_tasks=failed_tasks,
            system_load=cpu_usage,
            memory_usage=memory_usage,
            cpu_usage=cpu_usage,
            timestamp=datetime.utcnow()
        )
    
    def get_workflow_analytics(self, workflow_id: str) -> WorkflowAnalytics:
        """Get analytics for a specific workflow"""
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Get run statistics
        total_runs = self.db.query(WorkflowRun).filter(WorkflowRun.workflow_id == workflow_id).count()
        successful_runs = self.db.query(WorkflowRun).filter(
            and_(WorkflowRun.workflow_id == workflow_id, WorkflowRun.status == PipelineRunStatus.SUCCESS)
        ).count()
        failed_runs = self.db.query(WorkflowRun).filter(
            and_(WorkflowRun.workflow_id == workflow_id, WorkflowRun.status == PipelineRunStatus.FAILED)
        ).count()
        
        success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
        
        # Calculate average duration
        completed_runs = self.db.query(WorkflowRun).filter(
            and_(
                WorkflowRun.workflow_id == workflow_id,
                WorkflowRun.status == PipelineRunStatus.SUCCESS,
                WorkflowRun.started_at.isnot(None),
                WorkflowRun.completed_at.isnot(None)
            )
        ).all()
        
        if completed_runs:
            durations = []
            for run in completed_runs:
                duration = (run.completed_at - run.started_at).total_seconds()
                durations.append(duration)
            avg_duration = np.mean(durations)
        else:
            avg_duration = None
        
        # Get last run
        last_run = self.db.query(WorkflowRun).filter(
            WorkflowRun.workflow_id == workflow_id
        ).order_by(desc(WorkflowRun.created_at)).first()
        
        # Get most used nodes
        node_usage = self.db.query(
            WorkflowTask.node_id,
            func.count(WorkflowTask.id).label('usage_count')
        ).join(WorkflowRun).filter(
            WorkflowRun.workflow_id == workflow_id
        ).group_by(WorkflowTask.node_id).order_by(desc('usage_count')).limit(5).all()
        
        most_used_nodes = [
            {"node_id": node_id, "usage_count": count}
            for node_id, count in node_usage
        ]
        
        return WorkflowAnalytics(
            workflow_id=workflow_id,
            total_runs=total_runs,
            successful_runs=successful_runs,
            failed_runs=failed_runs,
            average_duration=avg_duration,
            success_rate=success_rate,
            last_run=last_run.created_at if last_run else None,
            most_used_nodes=most_used_nodes
        )
    
    def get_recent_alerts(self, limit: int = 50) -> List[Alert]:
        """Get recent alerts"""
        alerts_data = self.redis.lrange("metropolis:alerts", 0, limit - 1)
        alerts = []
        
        for alert_data in alerts_data:
            try:
                alert_dict = json.loads(alert_data)
                alert = Alert(**alert_dict)
                alerts.append(alert)
            except Exception as e:
                logger.error(f"Error parsing alert: {e}")
        
        return alerts
    
    async def send_webhook(self, event: WebhookEvent, webhook_url: str, secret: str = None):
        """Send webhook notification"""
        import aiohttp
        
        payload = {
            "event_type": event.event_type,
            "workflow_id": str(event.workflow_id),
            "run_id": str(event.run_id) if event.run_id else None,
            "task_id": str(event.task_id) if event.task_id else None,
            "status": event.status,
            "timestamp": event.timestamp.isoformat(),
            "data": event.data
        }
        
        headers = {"Content-Type": "application/json"}
        if secret:
            # Add webhook signature
            import hmac
            import hashlib
            signature = hmac.new(
                secret.encode(),
                json.dumps(payload).encode(),
                hashlib.sha256
            ).hexdigest()
            headers["X-Webhook-Signature"] = f"sha256={signature}"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(webhook_url, json=payload, headers=headers) as response:
                    if response.status >= 400:
                        logger.error(f"Webhook failed: {response.status}")
        except Exception as e:
            logger.error(f"Error sending webhook: {e}")
