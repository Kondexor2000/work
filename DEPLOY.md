Short deployment checklist

1) Prepare environment
- Copy `.env.example` to `.env` and set values (SECRET_KEY, DEBUG=False, ALLOWED_HOSTS, DATABASE_URL or USE_LOCAL_DB etc.)

2) Install Python deps (use virtualenv/venv)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

3) Database migrations

```powershell
cd C:\Users\kondz\work
python manage.py makemigrations
python manage.py migrate
```

Note: If `makemigrations` fails locally with "ModuleNotFoundError: No module named 'django'" activate the virtualenv and install requirements first.

4) Create superuser (optional)

```powershell
python manage.py createsuperuser
```

5) Collect static files (production)

```powershell
python manage.py collectstatic --noinput
```

6) Run server (development)

```powershell
python manage.py runserver
```

7) Troubleshooting
- If migrations reference model changes that require data migration, create a manual data migration or backup DB before migrating.
- For production deployments: use Gunicorn/ASGI + Nginx, set `DEBUG=False`, configure `ALLOWED_HOSTS`, and serve static via WhiteNoise or CDN.

8) Quick commands summary

```powershell
# Activate env
.\.venv\Scripts\Activate.ps1
# Install
pip install -r requirements.txt
# Migrate
python manage.py makemigrations
python manage.py migrate
# Create superuser
python manage.py createsuperuser
# Collect static
python manage.py collectstatic --noinput
# Run
python manage.py runserver 0.0.0.0:8000
```

If you want, I can:
- attempt to run migrations here (requires Django installed in this environment) — I tried and the runner returned "ModuleNotFoundError: No module named 'django'"; or
- generate a data migration for converting any OffersJobUser OneToOne→ForeignKey if needed; or
- continue scanning `workapp/views.py` and apply `select_related`/`prefetch_related` to more querysets.
