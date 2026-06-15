# AI Backlog

A Flask web app that turns natural-language product prompts into structured agile artefacts. Stakeholders write a free-form description, the OpenAI API produces a fully-formed user story via Pydantic structured outputs, and the result is persisted in a PostgreSQL database via SQLAlchemy. From the UI, each story can spawn a list of implementation tasks (again AI-generated) that are stored and displayed in a tasks view.

The codebase follows SOLID principles with a clear **Controller → Service → Repository → Model** layering and per-request dependency injection. See [`CLAUDE.md`](./CLAUDE.md) for the architecture details.

## Features

- Generate user stories from a prompt and store them in Postgres.
- For each story, generate granular implementation tasks (title, description, priority, effort, status, assignee) in one call.
- Tailwind-based UI to browse stories and tasks.
- Pydantic models double as the OpenAI structured-output schemas, so the AI cannot return free-form text.

## Tech stack

- Flask 3 + Flask-SQLAlchemy 3 + SQLAlchemy 2
- PostgreSQL via psycopg v3 (`psycopg[binary]`)
- OpenAI Python SDK (`beta.chat.completions.parse` with Pydantic `response_format`)
- Tailwind CSS (CDN, no build step)

## Project layout

```
app/
├── __init__.py           # Flask app factory
├── config.py             # env-driven configuration
├── extensions.py         # SQLAlchemy() singleton
├── container.py          # composition root / DI
├── models/               # SQLAlchemy models + enums
├── schemas/              # Pydantic schemas (response + AI-generation)
├── repositories/         # data access layer (ABCs + impls)
├── services/             # business logic + AI service
├── controllers/          # Flask blueprints (HTTP layer)
└── templates/            # Tailwind Jinja2 templates
run.py                    # entrypoint
requirements.txt
.env.example
```

## Prerequisites

- Python 3.9+
- A PostgreSQL database (local or hosted)
- An OpenAI API key

## Run locally

```bash
# 1. Clone and enter the project
git clone <your-repo-url> proyecto_3
cd proyecto_3

# 2. Create a virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

# 3. Configure environment variables
cp .env.example .env
# then edit .env and set DATABASE_URL and OPENAI_API_KEY

# 4. Start a Postgres database (skip if you already have one)
docker run --name proyecto3-db \
  -e POSTGRES_USER=user \
  -e POSTGRES_PASSWORD=password \
  -e POSTGRES_DB=proyecto_3 \
  -p 5432:5432 -d postgres:16

# 5. Run the app (auto-creates the schema on first boot)
.venv/bin/python run.py
```

Then open <http://localhost:5000>. You will be redirected to `/user-stories` where you can paste a prompt and generate your first story.

## API & Swagger documentation

Alongside the HTML UI the app exposes a JSON API:

| Method | Path                                                | Description                                |
| ------ | --------------------------------------------------- | ------------------------------------------ |
| GET    | `/api/v1/user-stories`                              | List every stored user story.              |
| POST   | `/api/v1/user-stories`                              | Generate a user story from `{ "prompt" }`. |
| GET    | `/api/v1/user-stories/{id}`                         | Get a single user story.                   |
| GET    | `/api/v1/user-stories/{id}/tasks`                   | List the tasks for a user story.           |
| POST   | `/api/v1/user-stories/{id}/generate-tasks`          | Generate and store tasks for that story.   |

Interactive documentation:

- **Swagger UI:** <http://localhost:5000/docs/>
- **Raw OpenAPI 3 spec:** <http://localhost:5000/openapi.json>

The spec is generated at runtime from the Pydantic schemas (`app/api/openapi.py`), so any field change to `UserStorySchema`, `TaskSchema`, or the `*GenerationSchema` models is reflected in the docs automatically. Each path includes a request/response example for the "Try it out" panel.

Quick smoke test with curl:

```bash
curl -s -X POST http://localhost:5000/api/v1/user-stories \
  -H 'Content-Type: application/json' \
  -d '{"prompt": "Marketing wants to export the campaign dashboard as a PDF."}'
```

### Environment variables

| Name             | Required | Default        | Notes                                                                  |
| ---------------- | -------- | -------------- | ---------------------------------------------------------------------- |
| `DATABASE_URL`   | yes      | —              | `postgres://`, `postgresql://`, `postgresql+psycopg://` all supported. |
| `OPENAI_API_KEY` | yes      | —              | Used to call the OpenAI API.                                           |
| `OPENAI_MODEL`   | no       | `gpt-4o-mini`  | Any chat model that supports structured outputs.                       |
| `SECRET_KEY`     | no       | `dev-secret-…` | Set in production so `flash()` cookies are signed properly.            |

## Deploy to the cloud

The app is a vanilla WSGI Flask app, so any platform that runs Python or Docker works. Two paths are documented below.

### Option A — Render (Python service, no Docker required)

1. Push the repo to GitHub.
2. In the [Render dashboard](https://dashboard.render.com), create a **PostgreSQL** database and copy its *Internal Database URL*.
3. Create a new **Web Service** from the GitHub repo with:
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `gunicorn run:app --bind 0.0.0.0:$PORT --workers 2`

   Render defaults new services to Python 3.14, but `pydantic-core` (a dependency of this project) has no pre-built wheel for 3.14 yet, so pip tries to compile it with Rust and the build fails. This repo pins Python via a tracked `.python-version` file (`3.12`). **Until that file is pushed**, set the `PYTHON_VERSION` environment variable in the Render dashboard to a full version such as `3.12.11` (Settings → Environment → Add variable).
   - **Environment variables:**
     - `DATABASE_URL` → the internal URL from step 2
     - `OPENAI_API_KEY` → your key
     - `SECRET_KEY` → any long random string
4. Deploy. The first request will create the tables via `db.create_all()`.

Render injects `$PORT` automatically; the `--bind` flag above honours it.

### Option B — Container image (Fly.io, Google Cloud Run, AWS App Runner, …)

Add this `Dockerfile` to the project root:

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --upgrade pip \
 && pip install -r requirements.txt \
 && pip install gunicorn

COPY . .

EXPOSE 8000
CMD ["gunicorn", "run:app", "--bind", "0.0.0.0:8000", "--workers", "2"]
```

Build and push:

```bash
docker build -t ai-backlog:latest .
docker run --rm -p 8000:8000 \
  -e DATABASE_URL=... \
  -e OPENAI_API_KEY=... \
  -e SECRET_KEY=... \
  ai-backlog:latest
```

Deployment commands per platform:

- **Fly.io:** `fly launch` (uses the Dockerfile), then `fly secrets set DATABASE_URL=... OPENAI_API_KEY=... SECRET_KEY=...` and `fly deploy`. Provision Postgres with `fly postgres create` and attach with `fly postgres attach`.
- **Google Cloud Run:** `gcloud run deploy ai-backlog --source . --region <region> --allow-unauthenticated --set-env-vars OPENAI_API_KEY=...,SECRET_KEY=... --set-secrets DATABASE_URL=projects/.../secrets/db-url:latest`. Use Cloud SQL for the database.
- **AWS App Runner:** push the image to ECR and create a service from it; set the same env vars in the App Runner console. Use RDS for Postgres.

### Production notes

- Replace `python run.py` with **gunicorn** (or another WSGI server) — Flask's built-in server is dev-only.
- The schema is created on boot via `db.create_all()`. For evolving schemas, introduce Alembic before relying on this in production.
- Set a strong, persistent `SECRET_KEY`; otherwise sessions/flash cookies invalidate on restart.
- Egress to `api.openai.com` is required from your runtime.
