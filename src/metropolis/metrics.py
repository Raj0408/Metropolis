# src/metropolis/metrics.py

from prometheus_client import Counter, Gauge

JOBS_PROCESSED_COUNTER = Counter(
    'metropolis_jobs_processed_total',
    'Total number of jobs processed',
    ['final_status'] # 'success' or 'failed'
)

READY_QUEUE_GAUGE = Gauge(
    'metropolis_ready_queue_depth_total',
    'Current number of jobs in the Redis ready_queue'
)

DELAYED_QUEUE_GAUGE = Gauge(
    'metropolis_delayed_queue_depth_total',
    'Current number of jobs in the delayed_queue'
)