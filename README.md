# AAfri Ride Backend

This repository contains a Django + DRF backend for the AAfri ride mobile application.

Features included in scaffold:
- Custom `User` model with `customer` and `rider` roles
- JWT authentication via `djangorestframework-simplejwt`
- OTP generation + verification endpoints (simple model-based OTP)
- `trips` app with basic lifecycle: create, accept, start, end, cancel
- PostgreSQL-ready config with SQLite fallback for local development
- Docker + docker-compose setup with Postgres and Redis
- OpenAPI docs via `drf-spectacular`

Quickstart (local development)

1. Copy `.env.example` to `.env` and edit settings.

2. Build and run with Docker Compose:

```powershell
cd "c:\Users\USER\Desktop\AAfri ride\backend"
docker-compose up --build
```

3. Run migrations (if not already run by entry command):

```powershell
docker-compose exec web python manage.py migrate
```

4. Create superuser:

```powershell
docker-compose exec web python manage.py createsuperuser
```

5. API docs available at `http://localhost:8000/api/docs/`.

Notes:
- This is a scaffold intended to be extended. Payment gateways, push notifications, and real SMS should be integrated in production.
- Use `MEDIA_ROOT` for uploads; in Docker Compose it's mounted to `./media`.

Deployment on Railway (non-Docker)
1. Push this repository to GitHub and connect it to Railway (or use the Railway CLI).
2. Set environment variables in Railway settings (minimum):
	- `SECRET_KEY` (strong random value)
	- `DEBUG=false`
	- `ALLOWED_HOSTS` (your Railway app host or `*` for testing)
	- `DATABASE_URL` (Railway-provided Postgres URL)
	- `REDIS_URL` (if using Celery)
	- `USE_S3=true` and `AWS_*` vars (if using S3 for media)
3. Railway will detect Python and install `requirements.txt`. The Procfile in this repo starts Gunicorn.
4. After the first deploy run migrations and collectstatic via Railway CLI or web console:
```powershell
railway run python manage.py migrate
railway run python manage.py collectstatic --noinput
```

Using Docker on Railway
- Railway also supports deploying via a `Dockerfile`. This repo already contains a `Dockerfile` at the project root. If you prefer container deployments, connect the repo and choose Docker deployment in Railway.

Notes on static & media
- Static: this project uses Whitenoise to serve static files. `collectstatic` must be run after deploy.
- Media: Railway's filesystem is ephemeral. Use an object store (S3) for user uploads. Enable S3 by setting `USE_S3=true` and the AWS environment variables.

Troubleshooting
- If Railway fails to find a web start command, ensure the `Procfile` exists with the `web` entry above.
- If migrations fail, run them manually via `railway run` and check `DATABASE_URL`.

"# aafribackend" 
"# aafribackend" 
