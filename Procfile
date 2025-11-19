web: gunicorn backend_project.wsgi --bind 0.0.0.0:$PORT
# optional release step (run migrations during deploy) - use Railway CLI or hooks to run
# release: python manage.py migrate