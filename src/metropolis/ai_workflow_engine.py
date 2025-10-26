"""
Advanced AI Workflow Engine for Metropolis
Handles complex AI workflows with real-time execution, monitoring, and optimization
"""

import asyncio
import json
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from sqlalchemy.orm import Session
from redis import Redis
import numpy as np
from scipy.optimize import minimize

from .models import (
    Workflow, WorkflowRun, WorkflowTask, WorkflowNode, 
    NodeType, JobStatus, PipelineRunStatus, TaskLog
)
from .ai_schemas import WorkflowRunStatus, TaskStatus, SystemMetrics
from .broker import redis_client

logger = logging.getLogger(__name__)

class ExecutionStrategy(str, Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    OPTIMIZED = "optimized"
    ADAPTIVE = "adaptive"

@dataclass
class NodeExecutionContext:
    """Context for executing a workflow node"""
    node_id: str
    workflow_run_id: str
    input_data: Dict[str, Any]
    config: Dict[str, Any]
    dependencies: List[str]
    retry_count: int = 0
    max_retries: int = 3
    timeout: int = 300  # 5 minutes default

@dataclass
class ExecutionMetrics:
    """Metrics for workflow execution"""
    start_time: datetime
    end_time: Optional[datetime] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    network_io: float = 0.0
    disk_io: float = 0.0
    error_count: int = 0
    retry_count: int = 0

class AIWorkflowEngine:
    """
    Advanced AI Workflow Engine with intelligent execution strategies,
    real-time monitoring, and adaptive optimization
    """
    
    def __init__(self, db: Session, redis_client: Redis):
        self.db = db
        self.redis = redis_client
        self.execution_strategies = {
            NodeType.AI_MODEL: self._execute_ai_model,
            NodeType.DATA_PROCESSOR: self._execute_data_processor,
            NodeType.TRANSFORMER: self._execute_transformer,
            NodeType.CONDITIONAL: self._execute_conditional,
            NodeType.MERGER: self._execute_merger,
            NodeType.SPLITTER: self._execute_splitter,
            NodeType.CUSTOM: self._execute_custom
        }
        self.active_executions: Dict[str, ExecutionMetrics] = {}
        self.performance_history: Dict[str, List[float]] = {}
        
    async def execute_workflow(
        self, 
        workflow_id: str, 
        parameters: Dict[str, Any],
        execution_strategy: ExecutionStrategy = ExecutionStrategy.OPTIMIZED
    ) -> WorkflowRun:
        """Execute a workflow with the specified strategy"""
        
        workflow = self.db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            raise ValueError(f"Workflow {workflow_id} not found")
        
        # Create workflow run
        workflow_run = WorkflowRun(
            id=str(uuid.uuid4()),
            workflow_id=workflow_id,
            status=PipelineRunStatus.PENDING,
            parameters=parameters,
            created_at=datetime.utcnow()
        )
        self.db.add(workflow_run)
        self.db.commit()
        
        # Initialize execution metrics
        execution_id = str(uuid.uuid4())
        self.active_executions[execution_id] = ExecutionMetrics(start_time=datetime.utcnow())
        
        try:
            # Build execution graph
            execution_graph = self._build_execution_graph(workflow)
            
            # Choose execution strategy
            if execution_strategy == ExecutionStrategy.OPTIMIZED:
                execution_plan = self._optimize_execution_plan(execution_graph)
            elif execution_strategy == ExecutionStrategy.ADAPTIVE:
                execution_plan = self._adaptive_execution_plan(execution_graph)
            else:
                execution_plan = self._simple_execution_plan(execution_graph)
            
            # Execute workflow
            await self._execute_plan(workflow_run, execution_plan, parameters)
            
            workflow_run.status = PipelineRunStatus.SUCCESS
            workflow_run.completed_at = datetime.utcnow()
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}")
            workflow_run.status = PipelineRunStatus.FAILED
            workflow_run.completed_at = datetime.utcnow()
            
        finally:
            # Update execution metrics
            if execution_id in self.active_executions:
                self.active_executions[execution_id].end_time = datetime.utcnow()
                del self.active_executions[execution_id]
            
            self.db.commit()
            
        return workflow_run
    
    def _build_execution_graph(self, workflow: Workflow) -> Dict[str, Any]:
        """Build execution graph from workflow definition"""
        graph = {}
        nodes = self.db.query(WorkflowNode).filter(WorkflowNode.workflow_id == workflow.id).all()
        
        for node in nodes:
            graph[node.node_id] = {
                'node': node,
                'dependencies': self._get_node_dependencies(node, workflow.definition),
                'dependents': self._get_node_dependents(node, workflow.definition),
                'estimated_duration': self._estimate_node_duration(node),
                'resource_requirements': self._get_resource_requirements(node)
            }
        
        return graph
    
    def _get_node_dependencies(self, node: WorkflowNode, definition: Dict[str, Any]) -> List[str]:
        """Get dependencies for a node"""
        if 'connections' in definition:
            dependencies = []
            for connection in definition['connections']:
                if connection['target_node'] == node.node_id:
                    dependencies.append(connection['source_node'])
            return dependencies
        return []
    
    def _get_node_dependents(self, node: WorkflowNode, definition: Dict[str, Any]) -> List[str]:
        """Get dependents for a node"""
        if 'connections' in definition:
            dependents = []
            for connection in definition['connections']:
                if connection['source_node'] == node.node_id:
                    dependents.append(connection['target_node'])
            return dependents
        return []
    
    def _estimate_node_duration(self, node: WorkflowNode) -> float:
        """Estimate execution duration for a node based on historical data"""
        node_key = f"node_duration:{node.node_id}"
        historical_data = self.redis.lrange(node_key, 0, -1)
        
        if historical_data:
            durations = [float(d) for d in historical_data]
            return np.mean(durations) + np.std(durations)  # Mean + std for safety
        else:
            # Default estimates based on node type
            defaults = {
                NodeType.AI_MODEL: 30.0,
                NodeType.DATA_PROCESSOR: 10.0,
                NodeType.TRANSFORMER: 5.0,
                NodeType.CONDITIONAL: 1.0,
                NodeType.MERGER: 2.0,
                NodeType.SPLITTER: 1.0,
                NodeType.CUSTOM: 15.0
            }
            return defaults.get(node.node_type, 10.0)
    
    def _get_resource_requirements(self, node: WorkflowNode) -> Dict[str, float]:
        """Get resource requirements for a node"""
        requirements = {
            'cpu': 1.0,
            'memory': 512.0,  # MB
            'gpu': 0.0,
            'network': 0.0
        }
        
        # Adjust based on node type and config
        if node.node_type == NodeType.AI_MODEL:
            requirements['cpu'] = 2.0
            requirements['memory'] = 2048.0
            if 'gpu_required' in node.config and node.config['gpu_required']:
                requirements['gpu'] = 1.0
        
        return requirements
    
    def _optimize_execution_plan(self, execution_graph: Dict[str, Any]) -> List[List[str]]:
        """Create optimized execution plan using graph algorithms"""
        # Topological sort with optimization
        in_degree = {node_id: len(data['dependencies']) for node_id, data in execution_graph.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_plan = []
        
        while queue:
            # Group nodes that can run in parallel
            current_batch = []
            for node_id in queue[:]:
                if self._can_run_parallel(node_id, current_batch, execution_graph):
                    current_batch.append(node_id)
                    queue.remove(node_id)
            
            if current_batch:
                execution_plan.append(current_batch)
                
                # Update in-degrees and add new ready nodes
                for node_id in current_batch:
                    for dependent in execution_graph[node_id]['dependents']:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)
        
        return execution_plan
    
    def _can_run_parallel(self, node_id: str, current_batch: List[str], graph: Dict[str, Any]) -> bool:
        """Check if a node can run in parallel with current batch"""
        node_requirements = graph[node_id]['resource_requirements']
        
        # Check resource conflicts
        for batch_node in current_batch:
            batch_requirements = graph[batch_node]['resource_requirements']
            if (node_requirements['gpu'] > 0 and batch_requirements['gpu'] > 0):
                return False  # GPU conflict
        
        return True
    
    def _adaptive_execution_plan(self, execution_graph: Dict[str, Any]) -> List[List[str]]:
        """Create adaptive execution plan based on system resources"""
        system_metrics = self._get_system_metrics()
        
        # Adjust plan based on current system load
        if system_metrics.cpu_usage > 80:
            # Reduce parallelism
            max_parallel = 2
        elif system_metrics.memory_usage > 80:
            # Reduce memory-intensive tasks
            max_parallel = 3
        else:
            max_parallel = 5
        
        # Create plan with resource constraints
        plan = self._optimize_execution_plan(execution_graph)
        adaptive_plan = []
        
        for batch in plan:
            if len(batch) <= max_parallel:
                adaptive_plan.append(batch)
            else:
                # Split large batches
                for i in range(0, len(batch), max_parallel):
                    adaptive_plan.append(batch[i:i + max_parallel])
        
        return adaptive_plan
    
    def _simple_execution_plan(self, execution_graph: Dict[str, Any]) -> List[List[str]]:
        """Create simple sequential execution plan"""
        # Topological sort
        in_degree = {node_id: len(data['dependencies']) for node_id, data in execution_graph.items()}
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        execution_plan = []
        
        while queue:
            execution_plan.append([queue.pop(0)])
            
            # Update in-degrees
            for node_id in list(execution_graph.keys()):
                if node_id in queue:
                    continue
                for dependent in execution_graph[node_id]['dependents']:
                    in_degree[dependent] -= 1
                    if in_degree[dependent] == 0:
                        queue.append(dependent)
        
        return execution_plan
    
    async def _execute_plan(
        self, 
        workflow_run: WorkflowRun, 
        execution_plan: List[List[str]], 
        parameters: Dict[str, Any]
    ):
        """Execute the execution plan"""
        for batch in execution_plan:
            # Execute batch in parallel
            tasks = []
            for node_id in batch:
                task = asyncio.create_task(
                    self._execute_node(workflow_run, node_id, parameters)
                )
                tasks.append(task)
            
            # Wait for all tasks in batch to complete
            await asyncio.gather(*tasks, return_exceptions=True)
    
    async def _execute_node(
        self, 
        workflow_run: WorkflowRun, 
        node_id: str, 
        parameters: Dict[str, Any]
    ) -> WorkflowTask:
        """Execute a single workflow node"""
        # Get node from database
        node = self.db.query(WorkflowNode).filter(
            WorkflowNode.workflow_id == workflow_run.workflow_id,
            WorkflowNode.node_id == node_id
        ).first()
        
        if not node:
            raise ValueError(f"Node {node_id} not found")
        
        # Create task
        task = WorkflowTask(
            id=str(uuid.uuid4()),
            workflow_run_id=workflow_run.id,
            node_id=node_id,
            task_id=f"{workflow_run.id}_{node_id}",
            status=JobStatus.PENDING,
            input_data=parameters.get(node_id, {}),
            created_at=datetime.utcnow()
        )
        self.db.add(task)
        self.db.commit()
        
        try:
            # Update status
            task.status = JobStatus.RUNNING
            task.started_at = datetime.utcnow()
            self.db.commit()
            
            # Execute node
            context = NodeExecutionContext(
                node_id=node_id,
                workflow_run_id=workflow_run.id,
                input_data=task.input_data,
                config=node.config,
                dependencies=[]
            )
            
            result = await self._execute_node_type(node, context)
            
            # Update task with result
            task.status = JobStatus.SUCCESS
            task.output_data = result
            task.completed_at = datetime.utcnow()
            
            # Log success
            self._log_task_event(task, "INFO", f"Node {node_id} completed successfully")
            
        except Exception as e:
            logger.error(f"Node {node_id} execution failed: {e}")
            task.status = JobStatus.FAILED
            task.error_message = str(e)
            task.completed_at = datetime.utcnow()
            
            # Log error
            self._log_task_event(task, "ERROR", f"Node {node_id} failed: {e}")
            
        finally:
            self.db.commit()
            
        return task
    
    async def _execute_node_type(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute node based on its type"""
        executor = self.execution_strategies.get(node.node_type)
        if not executor:
            raise ValueError(f"No executor for node type {node.node_type}")
        
        return await executor(node, context)
    
    # Node execution strategies
    async def _execute_ai_model(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute AI model node"""
        # Simulate AI model execution
        await asyncio.sleep(2)  # Simulate processing time
        
        # Mock AI model result
        return {
            "predictions": [0.8, 0.6, 0.9],
            "confidence": 0.85,
            "model_version": "v1.0",
            "processing_time": 2.0
        }
    
    async def _execute_data_processor(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute data processor node"""
        await asyncio.sleep(1)
        
        # Mock data processing result
        return {
            "processed_records": 1000,
            "processing_time": 1.0,
            "output_format": "json"
        }
    
    async def _execute_transformer(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute transformer node"""
        await asyncio.sleep(0.5)
        
        return {
            "transformed_data": context.input_data,
            "transformation_type": node.config.get("type", "default")
        }
    
    async def _execute_conditional(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute conditional node"""
        condition = node.config.get("condition", "default")
        
        if condition == "success":
            return {"result": "success", "next_node": "success_path"}
        else:
            return {"result": "failure", "next_node": "failure_path"}
    
    async def _execute_merger(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute merger node"""
        await asyncio.sleep(0.2)
        
        return {
            "merged_data": context.input_data,
            "merge_strategy": node.config.get("strategy", "concat")
        }
    
    async def _execute_splitter(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute splitter node"""
        await asyncio.sleep(0.1)
        
        return {
            "split_data": [context.input_data],
            "split_count": 1
        }
    
    async def _execute_custom(self, node: WorkflowNode, context: NodeExecutionContext) -> Dict[str, Any]:
        """Execute custom node"""
        # This would integrate with custom user code
        await asyncio.sleep(1)
        
        return {
            "custom_result": "executed",
            "custom_data": context.input_data
        }
    
    def _log_task_event(self, task: WorkflowTask, level: str, message: str, metadata: Dict[str, Any] = None):
        """Log task event"""
        log_entry = TaskLog(
            id=str(uuid.uuid4()),
            task_id=task.id,
            level=level,
            message=message,
            metadata=metadata or {},
            timestamp=datetime.utcnow()
        )
        self.db.add(log_entry)
    
    def _get_system_metrics(self) -> SystemMetrics:
        """Get current system metrics"""
        # This would integrate with actual system monitoring
        return SystemMetrics(
            active_workflows=len(self.active_executions),
            running_tasks=0,
            queued_tasks=0,
            failed_tasks=0,
            system_load=0.5,
            memory_usage=0.6,
            cpu_usage=0.4,
            timestamp=datetime.utcnow()
        )
    
    def get_workflow_status(self, workflow_run_id: str) -> WorkflowRunStatus:
        """Get real-time workflow status"""
        workflow_run = self.db.query(WorkflowRun).filter(WorkflowRun.id == workflow_run_id).first()
        if not workflow_run:
            raise ValueError(f"Workflow run {workflow_run_id} not found")
        
        tasks = self.db.query(WorkflowTask).filter(WorkflowTask.workflow_run_id == workflow_run_id).all()
        
        total_tasks = len(tasks)
        completed_tasks = len([t for t in tasks if t.status == JobStatus.SUCCESS])
        failed_tasks = len([t for t in tasks if t.status == JobStatus.FAILED])
        running_tasks = len([t for t in tasks if t.status == JobStatus.RUNNING])
        
        progress = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        return WorkflowRunStatus(
            run_id=workflow_run.id,
            workflow_id=workflow_run.workflow_id,
            status=workflow_run.status,
            progress=progress,
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            running_tasks=running_tasks,
            started_at=workflow_run.started_at,
            estimated_completion=None  # Could be calculated based on remaining tasks
        )
