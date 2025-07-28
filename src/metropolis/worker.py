# src/metropolis/worker.py (Heartbeat/Locking Version)

import time
import json
import threading
import sqlalchemy.orm

# Path setup
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metropolis import models
from metropolis.database import SessionLocal
from metropolis.broker import redis_client, READY_QUEUE_NAME, DEAD_LETTER_QUEUE_NAME,DELAYED_QUEUE_NAME
from metropolis.lua_scripts import COMPLETE_JOB_SCRIPT

LOCK_TTL_SECONDS = 300  # 5 minutes
HEARTBEAT_INTERVAL_SECONDS = 60 # 1 minute:
MAX_RETRY = 3
RETRY_DELAY_BASE_SECONDS = 10

def get_db() -> sqlalchemy.orm.Session:
    return SessionLocal()

complete_job_lua = redis_client.register_script(COMPLETE_JOB_SCRIPT)

def heartbeat(job_id: int, stop_event: threading.Event):
    lock_key = f"metropolis:job:{job_id}:lock"
    while not stop_event.wait(HEARTBEAT_INTERVAL_SECONDS):
        try:
            print(f"    ~ Heartbeat: Renewing lock for job {job_id}")
            redis_client.pexpire(lock_key, LOCK_TTL_SECONDS * 1000)
        except Exception as e:
            print(f"    ~ Heartbeat Error: Could not renew lock for job {job_id}: {e}")

def run_worker():
    print("--- Metropolis Worker is running (Locking & Heartbeat Mode) ---")
    print(f"Listening for jobs on queue: '{READY_QUEUE_NAME}'")
    
    while True:
        job_id_str = None
        job = None
        db = None
        heartbeat_thread = None
        stop_heartbeat = threading.Event()
        lock_key = None
        
        try:
            _, job_id_str = redis_client.blpop(READY_QUEUE_NAME, 0)
            job_id = int(job_id_str)
            lock_key = f"metropolis:job:{job_id}:lock"
            worker_id = f"worker-{os.getpid()}"

            if not redis_client.set(lock_key, worker_id, ex=LOCK_TTL_SECONDS, nx=True):
                print(f"[-] Could not acquire lock for job {job_id}. Another worker took it. Skipping.")
                continue # Go back to the start of the loop to get another job

            print(f"\n[+] Acquired lock for job {job_id}")

         
            heartbeat_thread = threading.Thread(target=heartbeat, args=(job_id, stop_heartbeat))
            heartbeat_thread.start()

            
            db = get_db()
            job = db.query(models.Job).filter(models.Job.id == job_id).first()

            if not job:
                print(f"[!] Error: Job with ID {job_id} not found. Skipping.")
                continue

            job.status = models.JobStatus.RUNNING
            db.commit()
            print(f"    -> Starting task: '{job.task_id}' for run_id: {job.pipeline_run_id}")

            
            time.sleep(3) 


            print(f"    -> Task '{job.task_id}' finished. Triggering completion script.")
            run_id = job.pipeline_run_id
            reverse_graph_key = f"metropolis:run:{run_id}:reverse_graph"
            downstream_job_ids_json = redis_client.hget(reverse_graph_key, str(job.id))
            downstream_job_ids = json.loads(downstream_job_ids_json) if downstream_job_ids_json else []
            deps_count_key = f"metropolis:run:{run_id}:deps_count"
            keys = [deps_count_key, READY_QUEUE_NAME]
            
            newly_ready_jobs = complete_job_lua(keys=keys, args=downstream_job_ids)
            print(f"    -> Atomically enqueued {len(newly_ready_jobs)} downstream jobs: {newly_ready_jobs}")

            job.status = models.JobStatus.SUCCESS
            db.commit()

            jobs_remaining_key = f"metropolis:run:{run_id}:jobs_count"
            jobs_left = redis_client.decr(jobs_remaining_key)

            print(f"    -> {jobs_left} jobs remaining for run {run_id}.")

            if jobs_left == 0:
                print(f"[CC] Run {run_id} has no jobs left. Marking as SUCCESS.")
                job.pipeline_run.status = models.PipelineRunStatus.SUCCESS
                db.commit()

        except Exception as e:
            print(f"[X] An unexpected error occurred: {e}")
            if db and job:
                job.retry_count += 1
                if job.retry_count > MAX_RETRY:
                    job.status = models.JobStatus.FAILED
                    job.logs = str(e)
                    redis_client.lpush(DEAD_LETTER_QUEUE_NAME,job.id)
                else:
                    delay = RETRY_DELAY_BASE_SECONDS * (2 ** (job.retry_count - 1))
                    retry_time_stamp = int(time.time()+delay)
                    print(f"    -> Scheduling job {job.id} for retry in {delay} seconds.")
                    redis_client.zadd(DELAYED_QUEUE_NAME,{job.id:retry_time_stamp})
                db.commit()
            else:
                print(f"    -> Could not process failure for job ID {job_id_str}, Janitor will recover.")

            time.sleep(1)
                
        finally:
            stop_heartbeat.set()
            if heartbeat_thread and heartbeat_thread.is_alive():
                heartbeat_thread.join()
            
            if lock_key:
                print(f"    -> Releasing lock for job {job_id}")
                redis_client.delete(lock_key)

            if db:
                db.close()

if __name__ == "__main__":
    run_worker()