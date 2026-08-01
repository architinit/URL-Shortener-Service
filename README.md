# URL Shortener Service

A URL shortener built with Flask, going beyond a basic redirect service to include click
analytics, custom aliases, expiring links, and rate limiting.

**Live demo:** https://url-shortener-service-fa1w.onrender.com
(hosted on Render's free tier — spins down after inactivity, so the first request after
a while may take ~30-50s to wake up)

## Features

- Shorten any valid URL to a 6-character Base62 code
- Optional custom aliases (e.g. `/my-brand`)
- Optional link expiry (auto-expires after N days)
- Per-link click analytics: count, referrer, user agent, timestamp
- Rate limiting on link creation (10/minute per IP) to prevent abuse
- Simple web UI to create links and view recent activity

## Architecture

- **Backend**: Flask, application-factory pattern, Blueprint-based routes
- **Persistence**: SQLAlchemy ORM over SQLite (swap `DATABASE_URL` for Postgres in production),
  schema managed with Flask-Migrate/Alembic
- **Short code generation**: each link's auto-increment primary key is Base62-encoded and
  zero-padded to a fixed length — collision-free by construction, no retry loop needed
- **Frontend**: plain HTML/CSS/JS calling the JSON API (no build step required)

## Running locally

```bash
python -m venv venv
source venv/bin/activate  # or venv\Scripts\activate on Windows
pip install -r requirements.txt
export FLASK_APP=run.py  # set FLASK_APP=run.py on Windows
flask db upgrade
python run.py
```

Visit `http://localhost:5000`.

## Database migrations

Schema changes are managed with Flask-Migrate. After changing a model:

```bash
flask db migrate -m "describe the change"
flask db upgrade
```

## Running with Docker

```bash
docker compose up --build
```

## Running tests

```bash
pytest
```

## API

| Method | Endpoint              | Description                          |
|--------|------------------------|---------------------------------------|
| POST   | `/api/shorten`         | Create a short link                   |
| GET    | `/<short_code>`        | Redirect to the original URL          |
| GET    | `/api/stats/<code>`    | Click count + recent click metadata   |
| GET    | `/api/links`           | List recent links                     |

**Create a link:**

```bash
curl -X POST http://localhost:5000/api/shorten \
  -H "Content-Type: application/json" \
  -d '{"long_url": "https://example.com/some/very/long/path", "expires_in_days": 7}'
```
