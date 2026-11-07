# One image: React is built, then Django (gunicorn) serves the API + the built app.
FROM node:20-alpine AS web
WORKDIR /web
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.12-slim
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1
WORKDIR /app
COPY backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/ ./
COPY --from=web /web/dist /app/frontend_dist
ENV FRONTEND_DIST=/app/frontend_dist MEDIA_ROOT=/data/media
RUN mkdir -p /data/media
EXPOSE 8000
# DB settings and secrets come from environment variables (see backend/.env.example).
CMD ["sh", "-c", "python manage.py collectstatic --noinput && python manage.py migrate --noinput && python manage.py seed_sections && gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000} --workers 3"]
