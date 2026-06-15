# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

For end-user setup and cloud deployment, see [`README.md`](./README.md). This file focuses on what is non-obvious from the code.

## Commands

The project uses the local venv at `.venv/` (Python 3.9). Use the venv binaries directly — there is no Makefile or task runner.

```bash
# Install / refresh dependencies
.venv/bin/pip install -r requirements.txt

# Run the app (binds 0.0.0.0:5000). Requires DATABASE_URL and OPENAI_API_KEY.
.venv/bin/python run.py

# Smoke-test imports + route map + OpenAPI spec without hitting Postgres or OpenAI
DATABASE_URL='sqlite:///:memory:' OPENAI_API_KEY='dummy' .venv/bin/python -c "
from app import create_app
app = create_app()
client = app.test_client()
assert client.get('/openapi.json').status_code == 200
assert client.get('/docs/').status_code == 200
print('ok')
"
```

There is no test suite, linter, or formatter configured in this repo yet.

## Environment

Both env vars are **required at app construction time** — `app/config.py` raises `RuntimeError` if either is missing, so even the smoke test must set them. Copy `.env.example` to `.env`; `python-dotenv` is loaded inside `create_app()`.

- `DATABASE_URL` — Postgres URL. `app/config.py` rewrites `postgres://` and `postgresql://` to `postgresql+psycopg://` (psycopg v3, not psycopg2 — see "Driver choice" below).
- `OPENAI_API_KEY` — used by `AIService`.
- `OPENAI_MODEL` — optional, defaults to `gpt-4o-mini`.
- `SECRET_KEY` — optional, only matters in non-dev because `flash()` needs it.

## Architecture

The app is a layered Flask application: **Controller → Service → Repository → Model**, with an `AIService` injected into the services. Dependencies are wired per-request in `app/container.py` (composition root); blueprints call `get_user_story_service()` / `get_task_service()` instead of importing implementations directly. Repositories and the AI service expose ABCs (`IUserStoryRepository`, `ITaskRepository`, `IAIService`) and the services depend on those interfaces — keep this direction of dependency when adding features.

**Dual interface (HTML + JSON), one service layer.** Two blueprint families wrap the same services:

- `app/controllers/` — HTML/MVC endpoints rendering Jinja templates (`/user-stories`, `/user-stories/<id>/tasks`, and their POST counterparts).
- `app/api/` — JSON API under `/api/v1/user-stories[...]`, returning Pydantic-serialised payloads.

When adding behaviour, put it in a service so both stacks pick it up; do not duplicate logic in the controllers.

**Request flow for the two AI-driven endpoints:**

- `POST /user-stories` (form) and `POST /api/v1/user-stories` (JSON) → `UserStoryService.generate_and_store(prompt)` → `AIService.generate_user_story` returns a `UserStoryGenerationSchema` → `UserStoryRepository.create_from_generation` persists it.
- `POST /user-stories/<id>/generate-tasks` (form) and `POST /api/v1/user-stories/<id>/generate-tasks` (JSON) → `TaskService.generate_and_store(id)` loads the story, calls `AIService.generate_tasks(story)` for a `TaskListGenerationSchema`, then `TaskRepository.bulk_create_for_story` persists in one commit.

**Structured AI outputs.** `AIService` uses `client.beta.chat.completions.parse(..., response_format=<PydanticModel>)`. The Pydantic schemas in `app/schemas/` serve **two roles**: API/response shapes (`UserStorySchema`, `TaskSchema`, and their `*Schemas` collection wrappers) *and* OpenAI structured-output targets (`UserStoryGenerationSchema`, `TaskGenerationSchema`, `TaskListGenerationSchema`). The generation schemas set `ConfigDict(extra="forbid")` because OpenAI's strict mode rejects additional properties — preserve that when editing them.

**OpenAPI / Swagger.** `app/api/openapi.py` builds the spec at runtime from the Pydantic schemas via `pydantic.json_schema.models_json_schema(...)`, with a custom `GenerateJsonSchema` subclass that rewrites `$defs` refs to `#/components/schemas/...` so the spec stays valid OpenAPI 3.0.3. The spec is served at `GET /openapi.json` and the UI at `/docs/` (via `flask-swagger-ui`). Inline example values (`USER_STORY_EXAMPLE`, `TASK_EXAMPLE`, `CREATE_USER_STORY_REQUEST_EXAMPLE`) live in the same module. **Any field change to a Pydantic schema is reflected in the docs automatically** — do not hand-edit JSON schemas anywhere else.

**Models.** `UserStory ↔ Task` is one-to-many with `cascade="all, delete-orphan"` on the parent side and `ON DELETE CASCADE` on the FK. `Priority` is shared between both tables and stored as a Postgres enum named `priority_enum`; `TaskStatus` uses `task_status_enum`. `created_at` is filled by the DB via `server_default=func.now()`, never by Python. `db.create_all()` runs inside `create_app()`, so adding columns to existing tables requires a manual migration — there is no Alembic setup.

**Templating.** Tailwind is loaded from the CDN (`<script src="https://cdn.tailwindcss.com">`) in `base.html`; there is no build step. Shared UI helpers (priority/status badges) live in `app/templates/_macros.html` and are imported per template.

## Driver choice (don't revert to psycopg2)

The Apple stock Python 3.9 on macOS arm64 has no compatible `psycopg2-binary` wheel — the only available arm64 wheels are tagged `macosx_14_0` and pip will fall through to a source build that needs `pg_config`. We use `psycopg[binary]>=3.2.4,<3.3` (psycopg v3) instead, and `Config` rewrites both `postgres://` and `postgresql://` URLs to `postgresql+psycopg://` so SQLAlchemy picks the v3 dialect. If you switch driver, update both `requirements.txt` and the URL rewriting in `app/config.py`.
