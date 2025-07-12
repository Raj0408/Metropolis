from .schemas import PipelineCreate
import queue

def validate_pipeline_dag(db_pipeline:PipelineCreate) -> bool:

    """
    Validates that the pipeline definition is a valid Directed Acyclic Graph (DAG).
    Uses Kahn's algorithm for topological sorting.

    Args:
        definition: The dictionary of tasks from the pipeline schema.

    Raises:
        ValueError: If a cycle is detected in the graph or if a dependency
                    points to a non-existent task.
    """


    definition = db_pipeline.definition
    nodes = {}
    in_degree = {}
    edges = {}
    queue_for = queue.Queue(maxsize=len(definition))
    for key,value in definition.items():
        nodes[key] = []
        in_degree[key] = len(value.dependencies)
        if in_degree[key]:
            for values in value.dependencies:
                nodes[key].append(values)
        else:
            queue_for.put(key)
    for key in definition:
        edges[key] = []
        for keys, values in nodes.items():
            if key in values:
                edges[key].append(keys)
    
    if(queue_for.qsize() == 0):
        return False
    travs = 0
    while(queue_for.qsize()):
        key = queue_for.get()
        print(key)
        travs = travs + 1
        for edg in edges[key]:
            print(edg)
            in_degree[edg] = in_degree[edg] - 1
            print(in_degree[edg])
            if in_degree[edg] == 0:
                queue_for.put(edg)
    
    if travs != len(definition):
        return False
    
    return True