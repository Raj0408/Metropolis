import time
import sqlalchemy.orm

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metropolis import models, crud
from metropolis.database import SessionLocal
from metropolis.broker import redis_client, READY_QUEUE_NAME

def get_db() -> sqlalchemy.orm.Session:
    return SessionLocal()



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

            print(f"    -> Task '{job.task_id}' completed successfully.")
            job.status = models.JobStatus.SUCCESS
            db.commit()
        except Exception as e:
            print(f"[X] An unexpected error occurred: {e}")
            if db and job:
                job.status = models.JobStatus.FAILED
                job.logs = str(e)
                db.commit()

            time.sleep(10)
        finally:
            if db:
                db.close()


if __name__ == "__main__":
    run_worker()

            

            

        


