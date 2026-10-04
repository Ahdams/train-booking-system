# Train Booking System Backend

FastAPI + PostgreSQL backend foundation for the train booking system.

## Run with Docker

```bash
docker compose up --build
```

API: `http://localhost:8000`

Health check: `http://localhost:8000/api/health`

Interactive API docs: `http://localhost:8000/docs`

## Run locally

Create a virtual environment, install `requirements.txt`, configure `DATABASE_URL` from `.env.example`, then run:

```bash
uvicorn app.main:app --reload
```

The frontend/localStorage version remains on `main`. This branch is the backend migration work.
