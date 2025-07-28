import json
import time
import sqlalchemy.orm

import sys
import os,threading,time
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from metropolis import models, crud
from metropolis.database import SessionLocal
from metropolis.broker import redis_client, READY_QUEUE_NAME, DELAYED_QUEUE_NAME

def get_db() -> sqlalchemy.orm.Session:
    return SessionLocal()


janitor_time = 30 #30 Sec for now

def zombie_job_checker():
    db = get_db()
    try:
        print("\n[J] Janitor waking up. Searching for stuck jobs...")
        running_job = db.query(models.Job).filter(
                models.Job.status == models.JobStatus.RUNNING
        ).all()

        if not running_job:
            print("[J] No running jobs found. All clear.")
        
        else:
            z_count = 0
            for job in running_job:
                lock_key = f"metropolis:job:{job.id}:lock"

                if not redis_client.exists(lock_key):
                    z_count += 1

                    job.status = models.JobStatus.QUEUED
                    redis_client.rpush(READY_QUEUE_NAME,job.id)
            db.commit()
    except Exception as e:
        print(f"[X] Janitor encountered an error: {str(e)}")
    
    finally:
        if db:
            db.close()

def requeue_delayed_jobs():
    """
    Checks the delayed queue (a sorted set) for jobs that are due to be retried.
    """
    print("[J] Checking for delayed jobs to requeue...")
    
    current_time = int(time.time())
    jobs_to_requeue = redis_client.zrangebyscore(DELAYED_QUEUE_NAME, 0, current_time)

    if not jobs_to_requeue:
        return # Nothing to do

    print(f"[J] Found {len(jobs_to_requeue)} jobs to requeue: {jobs_to_requeue}")

   
    with redis_client.pipeline() as pipe:
        pipe.rpush(READY_QUEUE_NAME, *jobs_to_requeue)
        pipe.zremrangebyscore(DELAYED_QUEUE_NAME, 0, current_time)
        pipe.execute()


def run_janitor():

    db = None
    print("--- Metropolis Janitor is running ---")
    print(f"Scanning for zombie jobs every {janitor_time} seconds.")
    while True:
            zombie_job_checker()
            requeue_delayed_jobs()
            time.sleep(janitor_time)

if __name__ == "__main__":
    run_janitor()
