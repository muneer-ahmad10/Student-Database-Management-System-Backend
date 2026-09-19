# Student Database Management System — Backend

A modular FastAPI backend for managing students, courses, and enrollments,
with an integrated **LangGraph + Gemini chatbot** that queries the database
in natural language, and a **Chroma vector store** for semantic search over
student profiles.

## Features

- ✅ Full CRUD for **Students**, **Courses**, and **Enrollments** (many-to-many with grades/status)
- ✅ Clean modular architecture: `models → schemas → crud → api` layers, fully separated
- ✅ Auto-generated interactive docs via **FastAPI Swagger UI** (`/docs`) and ReDoc (`/redoc`)
- ✅ **AI chatbot** (`/api/v1/chatbot/chat`) built with **LangGraph**, powered by **Gemini**,
  with read-only tools that query the live student DB (exact lookups + semantic search)
- ✅ **Vector database exploration** using **Chroma**, embedding student bios with Gemini
  embeddings for meaning-based search (e.g. "students interested in robotics")
- ✅ Dockerized as a deployable service (`Dockerfile` + `docker-compose.yml`)
- ✅ Pagination, search/filtering, and proper HTTP status codes on every endpoint
- ✅ Basic pytest suite (`tests/`)

## Architecture

```
student_db_backend/
├── app/
│   ├── main.py                 # FastAPI app, lifespan, CORS, router mounting
│   ├── config.py                # Centralized settings (pydantic-settings)
│   ├── database.py              # SQLAlchemy engine/session/Base
│   ├── models/                  # SQLAlchemy ORM models (one file per entity)
│   │   ├── student.py
│   │   ├── course.py
│   │   └── enrollment.py        # association object (many-to-many + grade/status)
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── student.py
│   │   ├── course.py
│   │   └── enrollment.py
│   ├── crud/                    # Pure DB-access functions, no HTTP concerns
│   │   ├── student.py
│   │   ├── course.py
│   │   └── enrollment.py
│   ├── api/v1/
│   │   ├── router.py             # aggregates all endpoint routers
│   │   └── endpoints/
│   │       ├── students.py       # /api/v1/students CRUD
│   │       ├── courses.py        # /api/v1/courses CRUD
│   │       ├── enrollments.py    # /api/v1/enrollments CRUD
│   │       └── chatbot.py        # /api/v1/chatbot/chat, /reindex
│   └── chatbot/
│       ├── graph.py              # LangGraph agent graph (Gemini + tools)
│       ├── tools.py              # DB-query tools exposed to the agent
│       └── vector_store.py       # Chroma vector DB wrapper
├── tests/
│   └── test_students.py
├── seed_data.py                  # populates sample students/courses/enrollments
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
└── .env.example
```

**Why this layering?** Each layer has one job — `models` define storage,
`schemas` define the API contract, `crud` holds business/DB logic, `api`
handles HTTP concerns only. This makes the codebase easy to test, extend
(e.g. swap SQLite → Postgres, or add a new entity), and reason about.

## Quick Start (local, no Docker)

```bash
cd student_db_backend
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env and set GOOGLE_API_KEY=<your Gemini key> to enable the chatbot
# (get one free at https://aistudio.google.com/app/apikey)

# Optional: load sample data
python seed_data.py

uvicorn app.main:app --reload
```

Then open:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc
- **Health check:** http://localhost:8000/health

## Quick Start (Docker)

```bash
cp .env.example .env   # set GOOGLE_API_KEY inside
docker compose up --build
```

The API is then live at `http://localhost:8000`, with the SQLite DB file and
Chroma vector store persisted in named Docker volumes across restarts.

To swap SQLite for Postgres in production, uncomment the `postgres` service
in `docker-compose.yml` and set `DATABASE_URL` accordingly — no application
code changes needed, since SQLAlchemy abstracts the dialect.

## API Overview

| Method | Endpoint | Description |
|---|---|---|
| POST | `/api/v1/students` | Create a student |
| GET | `/api/v1/students` | List students (pagination, search, filters) |
| GET | `/api/v1/students/{id}` | Get one student + their enrollments |
| PUT/PATCH | `/api/v1/students/{id}` | Update a student |
| DELETE | `/api/v1/students/{id}` | Delete a student |
| POST | `/api/v1/courses` | Create a course |
| GET | `/api/v1/courses` | List courses |
| GET/PUT/PATCH/DELETE | `/api/v1/courses/{id}` | Get/update/delete a course |
| POST | `/api/v1/enrollments` | Enroll a student in a course |
| GET | `/api/v1/enrollments` | List enrollments (filter by student/course) |
| GET/PUT/PATCH/DELETE | `/api/v1/enrollments/{id}` | Get/update/delete an enrollment |
| POST | `/api/v1/chatbot/chat` | Ask the AI assistant a question about the DB |
| POST | `/api/v1/chatbot/reindex` | Rebuild the vector index from current student bios |

Full request/response schemas, validation rules, and try-it-out consoles are
all available in Swagger UI at `/docs`.

## The AI Chatbot (LangGraph + Gemini)

`app/chatbot/graph.py` builds a small ReAct-style LangGraph:

```
START → agent (Gemini decides what to do)
           │
           ├─ needs data? → tools (query the DB) → back to agent
           └─ has answer? → END
```

The agent has access to **read-only** tools (`app/chatbot/tools.py`):

- `list_students_tool` / `get_student_detail_tool` — exact lookups
- `list_courses_tool` / `get_course_roster_tool` — course & roster queries
- `semantic_student_search_tool` — meaning-based search via the vector store
- `database_stats_tool` — quick counts

Example request:

```bash
curl -X POST http://localhost:8000/api/v1/chatbot/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Which students are majoring in Computer Science, and what is the roster for CS305?"}'
```

The chatbot is intentionally **read-only** — it explains that record changes
must go through the REST endpoints, keeping AI-driven mutation out of the
database for safety/auditability.

## Vector Database Exploration (Chroma)

`app/chatbot/vector_store.py` maintains a Chroma collection of embedded
student profiles (name, major, GPA, bio), using Gemini's embedding model.
This powers semantic search that plain SQL `LIKE` queries can't do — e.g.
"find students interested in AI research" matches on meaning, not keywords.

- Call `POST /api/v1/chatbot/reindex` after adding/editing student bios to
  refresh the index.
- If `GOOGLE_API_KEY` isn't set, the vector store falls back to a local
  default embedding model so it still works in offline/demo mode.

## Running Tests

```bash
pip install -r requirements.txt
pytest -q
```

Tests spin up an isolated in-memory SQLite database, so they never touch
real data.

## Notes on Production Hardening

This project is structured to be extended for production use:
- Swap `Base.metadata.create_all` for **Alembic** migrations (`alembic init`)
- Add authentication (e.g. OAuth2/JWT) via `app/core/security.py`
- Point `DATABASE_URL` at Postgres/MySQL (already supported, no code change)
- Add rate limiting / API keys in front of `/api/v1/chatbot/chat` to control Gemini spend
- Put the container behind a reverse proxy (nginx/Traefik) with TLS
