# Putting the site online

The Docker image runs everything as ONE service: Django serves the API and the built React app
from the same address, so login cookies and CSRF work without extra setup.
(The Docker build itself was not run while writing this project; if the build fails, send the error to Claude Code.)

## 1. What you need
- A host that runs Docker images (Render, Railway, Fly.io, or your own VPS).
- A PostgreSQL database.
- A persistent disk mounted at `/data` (so the uploaded logo survives restarts), or accept that the
  logo falls back to the built-in default after a restart.

## 2. Environment variables (set on the host, never in Git)
| Name | Value |
|---|---|
| `DJANGO_SECRET_KEY` | a long random string |
| `DJANGO_DEBUG` | `False` |
| `DJANGO_ALLOWED_HOSTS` | your domain, e.g. `coe-school.onrender.com` |
| `CSRF_TRUSTED_ORIGINS` | `https://your-domain` |
| `DJANGO_SECURE_COOKIES` | `True` |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | from your PostgreSQL service |
| `MEDIA_ROOT` | `/data/media` (already the default inside the image) |

## 3. First start
The container runs `collectstatic`, `migrate` and `seed_sections` by itself. Then, once, open the
service's shell and create the admin:
```
python manage.py create_admin
```
Log in at `https://your-domain/admin/login`.

## 4. Checklist
- Site opens over `https://`; register, approve as admin, log in as teacher and student.
- Excel upload and PDF download work. Logo upload survives a restart.
- `DJANGO_DEBUG=False`. Enable the host's automatic database backups.
- Media files are served by Django itself, which is fine for one small logo.

## Without Docker (VPS)
Install Python, Node, PostgreSQL and Nginx. Run `npm ci && npm run build` in `frontend/`, then in `backend/`:
`pip install -r requirements.txt`, `python manage.py collectstatic --noinput`, `python manage.py migrate`,
`python manage.py seed_sections`, `python manage.py create_admin`, and
`gunicorn config.wsgi:application --bind 127.0.0.1:8000`. Put Nginx with HTTPS (Let's Encrypt) in front of it.
