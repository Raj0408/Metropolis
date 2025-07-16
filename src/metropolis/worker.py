import json
import time
import sqlalchemy.orm

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metropolis import models, crud
from metropolis.database import SessionLocal
from metropolis.broker import redis_client, READY_QUEUE_NAME
from metropolis.lua_scripts import COMPLETE_JOB_SCRIPT

def get_db() -> sqlalchemy.orm.Session:
    return SessionLocal()


complete_job_lua = redis_client.register_script(COMPLETE_JOB_SCRIPT)

def run_worker():
    print("--- Metropolis Worker is running ---")
    print(f"Listening for jobs on queue: '{READY_QUEUE_NAME}'")
    while True:
        db = None

        try:
            _,job_id_str = redis_client.blpop(READY_QUEUE_NAME,0)
            job_id = int(job_id_str)

            print(f"\n[+] Received job with ID {job_id}")

            db = get_db()

            job = db.query(models.Job).filter(models.Job.id == job_id).first()

            if not job:
                print(f"[!] Error: Job with ID {job_id} not found in database. Skipping.")
                continue
            
            print(f"    -> Starting task: '{job.task_id}' for run_id: {job.pipeline_run_id}")
            job.status = models.JobStatus.RUNNING
            db.commit()


            time.sleep(5)


            reverse_graph_key = f"metropolis:run:{job.pipeline_run_id}:reverse_graph"
            
            depends_jobs_json = redis_client.hget(reverse_graph_key,str(job.id))
            
            depends_job_ids = json.loads(depends_jobs_json) if depends_jobs_json else []

            deps_count_key = f"metropolis:run:{job.pipeline_run_id}:deps_count"
            keys = [deps_count_key,READY_QUEUE_NAME]

            ready_jobs = complete_job_lua(keys=keys,args=depends_job_ids)

            print(f"    -> Atomically enqueued {len(ready_jobs)} downstream jobs: {ready_jobs}")


            
            job.status = models.JobStatus.SUCCESS
            db.commit()
        except Exception as e:
            print(f"[X] An unexpected error occurred: {e}")
            if db and job:
                job.status = models.JobStatus.FAILED
                job.logs = str(e)
                db.commit()

            time.sleep(5)


        finally:
            if db:
                db.close()


if __name__ == "__main__":
    run_worker()

            

            

        


