# Django ASR Gateway + UI (uses existing FastAPI ASR core)

## Run
```bash
sudo apt update && sudo apt install -y redis-server ffmpeg
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
python manage.py migrate
python manage.py createsuperuser

# terminal 1
python manage.py runserver 0.0.0.0:8000
uvicorn asr_gateway.asgi:application --host 127.0.0.1 --port 8000

# terminal 2
celery -A asr_gateway worker -l info
```

UI:
- http://127.0.0.1:8000/asr/
- http://127.0.0.1:8000/login/
- admin: /admin/

WebSocket:
- ws://HOST/ws/jobs/<job_id>/?token=<JWT>

Notes:
- audio bytes are not stored on disk.
- only transcript + metadata + accounting rows are stored.
