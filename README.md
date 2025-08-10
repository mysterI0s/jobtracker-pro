## JobTracker Pro

Track and aggregate remote job postings into a local database using Django, Scrapy, Celery, and Redis. The project scrapes job boards, normalizes data, and stores them in Django models for browsing and further processing.

### Key Features
- **Scraping pipeline**: Scrapy spiders (starting with WeWorkRemotely) fetch job postings.
- **Data normalization**: Validation and duplicate-filtering pipelines clean and de-duplicate items.
- **Persistence**: Items are written to Django models (`Company`, `JobSource`, `Job`, etc.).
- **Background processing**: Celery workers run scraping and maintenance tasks, with Redis as the broker/result backend.
- **Scheduling**: Periodic scraping and cleanup via Celery Beat.
- **Admin UI**: Manage data in Django Admin; seed sources via a management command.

---

## Architecture Overview

```
jobtracker-pro/
  apps/
    companies/        # Company and JobSource models
    jobs/             # Job and JobBookmark models, Celery tasks, management commands
  celery_app.py       # Celery app/bootstrap and schedules
  jobtracker/         # Django project (settings, URLs, WSGI/ASGI)
  scrapers/
    jobscraper/       # Scrapy project
      jobscraper/
        spiders/      # Spiders (e.g., weworkremotely)
        pipelines.py  # Duplicates, Validation, DjangoWriter pipelines
        items.py      # Django-backed items + raw helper fields
        settings.py   # Scrapy settings + Django initialization
  logs/               # django.log, scrapy.log
  templates/, static/ # Optional assets
```

### Major Components
- **Django models**
  - `apps.companies.models.Company`
  - `apps.companies.models.JobSource` (scraping source metadata, stats)
  - `apps.jobs.models.Job` (unique on `[source, external_id]`)
  - `apps.jobs.models.JobBookmark` (user bookmarks)
- **Scrapy**
  - Spider: `scrapers/jobscraper/jobscraper/spiders/weworkremotely.py`
  - Items: `scrapers/jobscraper/jobscraper/items.py` (uses `scrapy-djangoitem`)
  - Pipelines: `scrapers/jobscraper/jobscraper/pipelines.py`
  - Settings: `scrapers/jobscraper/jobscraper/settings.py` (initializes Django)
- **Celery**
  - Bootstrap: `celery_app.py`
  - Tasks: `apps/jobs/tasks.py` (scraping, cleanup, stats)

---

## Prerequisites
- Python 3.11+ (project is compatible with up-to-date Django/Scrapy versions)
- Redis 6+ (as message broker and result backend)
- Windows 10/11, macOS, or Linux

### Install Redis
- Docker (recommended):
  ```
  docker run -d --name jobtracker-redis -p 6379:6379 redis:7
  ```
- Windows (WSL2 Ubuntu):
  ```
  sudo apt update && sudo apt install -y redis-server
  sudo service redis-server start
  ```
- Native Windows alternative: Memurai (Redis-compatible)

---

## Setup
1) Clone and enter the repo.

2) Create and activate a virtual environment.
   - Windows PowerShell:
     ```
     python -m venv .\.venv
     .\.venv\Scripts\activate
     ```
   - macOS/Linux:
     ```
     python3 -m venv .venv
     source .venv/bin/activate
     ```

3) Install dependencies.
   ```
   pip install -r requirements.txt
   ```

4) Configure environment (create a `.env` in the repo root).
   ```
   SECRET_KEY=django-insecure-change-me
   DEBUG=true
   # Default Redis; override if using non-default host/DB
   REDIS_URL=redis://localhost:6379/0
   # Optional: switch to Postgres (requires dj-database-url)
   # DATABASE_URL=postgres://USER:PASSWORD@HOST:5432/DBNAME
   ```

5) Initialize the database.
   ```
   python manage.py migrate
   python manage.py createsuperuser
   ```

6) Seed initial job sources (optional but recommended).
   ```
   python manage.py create_sample_data
   ```

7) Run the development server.
   ```
   python manage.py runserver
   ```

Open Django Admin at `http://127.0.0.1:8000/admin/`.

---

## Celery & Redis

This project uses Celery for background tasks and Redis for the message broker/result backend.

### Configuration
Set in `jobtracker/settings/base.py` (overridable via `.env`):
```
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
CELERY_TIMEZONE=UTC
```

### Start Celery
- Windows PowerShell (use solo pool):
  ```
  .\.venv\Scripts\activate
  celery -A celery_app worker -l info -P solo
  ```
- Start the scheduler (Beat) in another terminal:
  ```
  .\.venv\Scripts\activate
  celery -A celery_app beat -l info
  ```
- Alternatively run worker + beat in one process (simpler):
  ```
  celery -A celery_app worker -l info -P solo -B
  ```

### Periodic tasks
Defined in `celery_app.py`:
- `apps.jobs.tasks.scrape_all_sources` every hour
- `apps.jobs.tasks.cleanup_old_jobs` daily at 02:00

Optional: manage schedules in the database via `django_celery_beat` by setting:
```
CELERY_BEAT_SCHEDULER=django_celery_beat.schedulers:DatabaseScheduler
```

---

## Scraping

There is a Scrapy project under `scrapers/jobscraper`. It initializes Django in `scrapers/jobscraper/jobscraper/settings.py` so items can be written directly to Django models.

### How Scrapy integrates with Django
- Adds the project root to `PYTHONPATH` so `jobtracker` is importable.
- Sets `DJANGO_SETTINGS_MODULE=jobtracker.settings`.
- Sets `DJANGO_ALLOW_ASYNC_UNSAFE=true` so Django ORM writes are allowed from Scrapy’s async event loop.
- Pipelines:
  - `DuplicatesPipeline`: drops repeated items within a run.
  - `ValidationPipeline`: validates and normalizes fields (title, salary, location, etc.).
  - `DjangoWriterPipeline`: creates/updates `Company` and `Job` rows and updates `JobSource` stats.

### Running scrapes
- Via management command (queues Celery task by default):
  ```
  # List sources
  python manage.py scrape_jobs --list-sources

  # Scrape one source (async via Celery)
  python manage.py scrape_jobs --source WeWorkRemotely --max-jobs 20

  # Scrape synchronously (runs in the current process)
  python manage.py scrape_jobs --source WeWorkRemotely --max-jobs 5 --sync
  ```

- Direct Scrapy usage (from `scrapers/jobscraper`):
  ```
  cd scrapers/jobscraper
  scrapy crawl weworkremotely -L INFO -s JOBTRACKER_MAX_JOBS_PER_RUN=5
  ```

### Current spider(s)
- `weworkremotely`:
  - Category listing pages in `start_urls`
  - Parses job links, follows to detail pages
  - Extracts fields using DOM selectors with fallbacks (meta tags, JSON-LD)
  - Heuristics to split combined “Company – Title” strings

### Adding a new source
1) Create a spider in `scrapers/jobscraper/jobscraper/spiders/`.
2) Add a `JobSource` row in the DB (via admin or `create_sample_data`).
3) Map the new source name to the spider in `apps/jobs/tasks.py` under `spider_mapping`.
4) Ensure the item fields are populated; extend pipelines as needed.

---

## Data Model (high-level)

- `Company`
  - `name`, `slug`, `website`, `industry`, `size`, social links
- `JobSource`
  - `name` (unique), `base_url`, `is_active`, scrape settings (`rate_limit`, `user_agent`)
  - `last_scraped`, `total_jobs_scraped`
- `Job`
  - `title`, `company` (FK), `source` (FK)
  - `external_id` (source-site ID), `url`
  - `description`, `requirements`, `benefits`
  - `location`, `is_remote`, `remote_type`
  - `job_type`, `experience_level`, salary fields
  - `posted_date`, `scraped_date`, `expires_date`, `is_active`
  - `tags` (JSON), `skills_required` (JSON)
  - Unique on `[source, external_id]`

---

## Configuration

Environment variables (via `.env` using `python-decouple`):
- `SECRET_KEY` (required)
- `DEBUG` (true/false)
- `REDIS_URL` (default `redis://localhost:6379/0`)
- `DATABASE_URL` (optional; falls back to SQLite when absent)
- `ALLOWED_HOSTS` (configure in `jobtracker/settings/base.py` for production)

Settings modules:
- Default import resolves to `jobtracker/settings/development.py` (via `jobtracker/settings/__init__.py`).
- For production, set:
  ```
  set DJANGO_SETTINGS_MODULE=jobtracker.settings.production    # Windows
  export DJANGO_SETTINGS_MODULE=jobtracker.settings.production  # macOS/Linux
  ```

Logging outputs to `logs/django.log` (Django) and `logs/scrapy.log` (Scrapy).

---

## Troubleshooting

- "ModuleNotFoundError: No module named 'jobtracker'" when running Scrapy
  - Ensure you run Scrapy from `scrapers/jobscraper` or use the provided management command. The Scrapy settings add the repo root to `PYTHONPATH`.

- "You cannot call this from an async context - use a thread or sync_to_async"
  - Scrapy runs under an async reactor; Django ORM is guarded by default. This project sets `DJANGO_ALLOW_ASYNC_UNSAFE=true` in Scrapy settings to allow writes.

- "Couldn't import Django" during `manage.py` commands
  - Activate the virtualenv: `.\.venv\Scripts\activate` (Windows) or `source .venv/bin/activate` (macOS/Linux).

- Naive datetime warnings for `posted_date`
  - The spider prefers JSON-LD timestamps; otherwise it falls back to `timezone.now()`. You can tune parsing in `weworkremotely._extract_posted_date`.

- Titles/companies show as "Unknown"
  - Selectors change frequently on job boards. The spider includes JSON-LD and meta fallbacks; further refine selectors if needed.

---

## Development

Common commands:
```
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
python manage.py create_sample_data
python manage.py scrape_jobs --list-sources
python manage.py scrape_jobs --source WeWorkRemotely --max-jobs 5 --sync
```

Run Celery locally (Windows PowerShell):
```
.\.venv\Scripts\activate
celery -A celery_app worker -l info -P solo
celery -A celery_app beat -l info
```

---

## Roadmap
- Additional spiders (RemoteOK, AngelList, and more)
- Richer parsing (structured salary/location, better date handling)
- REST API endpoints (DRF) for listing/filtering jobs
- Automated tests and CI

---

## Acknowledgements
- Built with Django, Scrapy, Celery, Redis.
- JSON-LD extraction where available to improve data quality.


