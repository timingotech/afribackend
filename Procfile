# Use Daphne as the ASGI server so Channels works for websocket routes
web: daphne -b 0.0.0.0 -p $PORT backend_project.asgi:application
# optional release step (run migrations during deploy) - use Railway CLI or hooks to run
# release: python manage.py migrate