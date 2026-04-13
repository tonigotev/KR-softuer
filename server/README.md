# GP Visits Scheduling API

Coursework backend implemented with Django REST Framework, JWT authentication, and Docker.

## Tech Stack

- Django + Django REST Framework
- JWT with `djangorestframework-simplejwt`
- PostgreSQL (Docker), SQLite fallback for local testing
- Docker + Docker Compose

## Quick Start (Docker)

```bash
docker compose up --build
```

API base URL: `http://localhost:8000/v1/`

Health endpoint: `http://localhost:8000/health/`

## Local Development (without Docker)

```bash
py -3.13 -m pip install -r requirements.txt
py -3.13 manage.py migrate
py -3.13 manage.py runserver
```

## Running Tests

```bash
py -3.13 manage.py test
py -3.13 -m coverage run manage.py test
py -3.13 -m coverage report
```

## Documentation

- API usage: [`docs/API_USAGE.md`](docs/API_USAGE.md)
- Architecture and design: [`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md)
- Self-analysis (clean code/SOLID): [`docs/SELF_ANALYSIS.md`](docs/SELF_ANALYSIS.md)
