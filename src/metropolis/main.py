from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from . import models
from .database import engine, get_db
from .settings import settings

# This command tells SQLAlchemy to create all tables based on our models.
# In a real production app, we would use Alembic for this, but for the first run, this is fine.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Metropolis - Pipeline Orchestrator")

@app.get("/")
def read_root():
    """A simple hello world endpoint to confirm the API is running."""
    return {"message": "Welcome to Metropolis API"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """
    A health check endpoint that confirms API and Database connectivity.
    """
    try:
        # A simple query to test the database connection
        db.execute("SELECT 1")
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {e}"

    return {
        "api_status": "ok",
        "database_status": db_status,
        "environment": settings.ENVIRONMENT
    }