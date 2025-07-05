# Metropolis 🏙️

**Metropolis** is a robust, production-grade platform for orchestrating complex data engineering and machine learning pipelines. It is built from the ground up on the principle of "Design for Failure," focusing on resilience, observability, and fault-tolerance.

This project is a deep dive into the engineering principles behind modern distributed systems, serving as a practical masterclass in building reliable, containerized applications.

---

## Architecture Overview

Metropolis is built on a microservices-style architecture, with clear separation of concerns between components. All services are containerized with Docker for portability and production-readiness.

1.  **Orchestration API (FastAPI):** The public-facing entry point. It handles:
    *   Pipeline definition submission and validation (ensuring it's a valid DAG).
    *   Triggering and parameterizing pipeline runs.
    *   Persisting all definitive state to the PostgreSQL database.
    *   Enqueuing the initial "root" jobs into Redis.

2.  **Permanent State / Source of Truth (PostgreSQL):**
    *   Stores immutable pipeline definitions, historical logs of all pipeline runs, and final job results. Designed for data integrity and relational consistency.

3.  **Broker / "Hot" State (Redis):**
    *   Manages the high-speed operational state: the queue of jobs ready for execution (`ready_queue`), real-time status of running jobs, job locks, and Dead Letter Queues (DLQ).

4.  **Artifact Store (MinIO):**
    *   An S3-compatible object storage for large data artifacts (e.g., datasets, trained models, evaluation reports) passed between tasks.

5.  **Worker Fleet (Python):**
    *   A pool of identical, stateless consumer processes that execute the actual pipeline tasks. They are designed to be resilient, handle errors with retries, and perform atomic state transitions using Redis Lua scripts.

6.  **Support Services (Python):**
    *   **Janitor:** A "reaper" process that finds and requeues jobs whose locks have expired due to a worker crash.
    *   **Scheduler:** (Future) A cron-based service for triggering time-based pipeline runs.

---

## Technology Stack

*   **Language:** Python 3.10+
*   **API Framework:** FastAPI
*   **Permanent State:** PostgreSQL
*   **Broker & Cache:** Redis
*   **Artifact Store:** MinIO (S3-compatible)
*   **Orchestration:** Docker & Docker Compose
*   **Database Migrations:** Alembic
*   **Data Schemas:** Pydantic

---

## Getting Started

### Prerequisites

*   Docker
*   Docker Compose
*   Python 3.10+ (for local development, if not using Docker exclusively)

### Installation & Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/yraj0408/metropolis.git
    cd metropolis
    ```

2.  **Configure Environment Variables:**
    The application uses environment variables for configuration. Create a `.env` file from the example.
    ```bash
    # This step will be added once we define the settings.
    # For now, this is a placeholder.
    cp .env.example .env
    ```
    *Note: The `.env` file is for local development and is excluded from Git via `.gitignore`.*

3.  **Build and Run the Services:**
    Use Docker Compose to build the images and start all the services.
    ```bash
    docker-compose up --build
    ```

4.  **Verify the API:**
    Once the containers are running, you can access the interactive API documentation (powered by Swagger UI) at:
    [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Project Roadmap

This project is being developed in distinct phases:

*   **Phase 1: The Unshakeable Core:** Build the API with robust DAG validation and persistence. Set up the core PostgreSQL and Redis layers. A submitted pipeline correctly enqueues its root nodes.
*   **Phase 2: The Resilient Worker & Atomic Transitions:** Implement the worker logic, atomic completion scripts (Lua), error handling, retries, and the Dead Letter Queue.
*   **Phase 3: Observability and Production Readiness:** Implement heartbeating/locking, the "Janitor" service, structured logging, metrics (Prometheus), and status-checking endpoints.
*   **Phase 4: The Advanced Orchestrator:** Add features like time-based scheduling, a simple UI, and distributed tracing.

---

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
