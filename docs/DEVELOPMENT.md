# Development Guide

This file is a short, non-destructive developer guide for working on the MyTypist backend. It documents key configuration flags added by the agent, how to run the app locally, migrations, Celery, and testing practices.

## Key configuration flags
These flags are environment variables read by `config.Settings`:

- `SKIP_DB_TABLE_CREATION` (default: `false`)
  - When `true`, the app will not attempt any automatic table creation at startup. Use Alembic for schema changes instead.

- `REDIS_ENABLED` (default: `false`)
  - When `true`, the app will try to connect to Redis using `REDIS_HOST`, `REDIS_PORT`, and `REDIS_PASSWORD`. If disabled or a connection fails, the app falls back to a local mock client (only when explicitly enabled/disabled in settings).

- `ENABLE_SYNC_THUMBNAILS` (default: `false`)
  - When `true`, the app may attempt to generate thumbnails synchronously during preview generation (only recommended for controlled dev environments). When `false`, thumbnail generation is deferred to asynchronous tasks or background workers.

- `THUMBNAILS_PATH` (default: `./storage/thumbnails`)
  - Where generated thumbnails are cached/stored.

## Local development - quickstart
1. Create a Python virtual environment and install dependencies (from workspace root):

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt  # or use pyproject/poetry if applicable
```

2. Create a `.env` file at the repository root and populate the essentials:

```
DATABASE_URL=postgresql://postgres:password@localhost:5432/mytypisdb
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_ENABLED=false
SKIP_DB_TABLE_CREATION=true
ENABLE_SYNC_THUMBNAILS=false
```

3. Run database migrations with Alembic (preferred):

```bash
alembic upgrade head
```

4. Start the FastAPI app locally:

```bash
python main.py
```

If you need auto-reload during development, ensure `DEBUG=true` in `.env` or use `uvicorn main:app --reload`.

## Running Celery
Start a worker (example using Redis broker):

```bash
celery -A main.celery_app worker --loglevel=info -Q document_processing,default
```

Adjust broker URL in env if using a different broker.

## Running tests
Run pytest from the workspace root. Tests in this repo use fixtures that may mock Redis and other services. Ensure you read `app/tests/conftest.py` for how fixtures work.

```bash
pytest -q
```

## Notes & best practices
- Do not move `attached_assets/`. These are user-provided documentation files and archives; do not modify or delete them. Treat `attached_assets/` as read-only documentation material.
- Prefer Alembic migrations over automatic model-based table creation. The repo includes `alembic/` for that purpose.
- Avoid enabling synchronous thumbnail generation in production. Use Celery and the `thumbnail_service` instead.
- If you enable `REDIS_ENABLED`, ensure a real Redis instance is available and reachable.

## Troubleshooting
- If `redis` connection fails, check `REDIS_HOST`/`REDIS_PORT`, and `REDIS_ENABLED`. The service may fallback to an in-memory mock if configured.
- If migrations fail, inspect `alembic/` and ensure the database user has permissions.

## Contact
If something in this guide is unclear or you want the agent to avoid touching a particular directory, add a short note in `docs/DEVELOPMENT.md` and the agent will treat that directory as read-only for future edits.
