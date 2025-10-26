from collections import deque
from typing import Dict
from .schemas import TaskDefinition 

def validate_pipeline_dag(definition: Dict[str, TaskDefinition]) -> bool:

    """
    Validates that the pipeline definition is a valid Directed Acyclic Graph (DAG).
    Uses Kahn's algorithm for topological sorting.

    Args:
        definition: The dictionary of tasks from the pipeline schema.

    Raises:
        ValueError: If a cycle is detected in the graph or if a dependency
                    points to a non-existent task.
    """

    graph = {task_id: [] for task_id in definition}
    in_degree = {task_id: 0 for task_id in definition}

    for task_id, task_def in definition.items():
        for dependency in task_def.dependencies:
            if dependency not in graph:
                raise ValueError(f"Task '{task_id}' has an invalid dependency: '{dependency}' does not exist.")
        
            graph[dependency].append(task_id)
            in_degree[task_id] += 1

    queue = deque([task_id for task_id, degree in in_degree.items() if degree == 0])
    
    if not queue and definition:
        raise ValueError("Invalid pipeline: a cycle was detected (no root nodes found).")

    sorted_nodes_count = 0
    while queue:
        current_task_id = queue.popleft()
        sorted_nodes_count += 1

        for dependent_task_id in graph[current_task_id]:
            in_degree[dependent_task_id] -= 1
            if in_degree[dependent_task_id] == 0:
                queue.append(dependent_task_id)

    if sorted_nodes_count != len(definition):
        raise ValueError("Invalid pipeline: a cycle was detected.")