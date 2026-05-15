"""
scheduler/celery_app.py — Configuración de Celery

Tareas programadas:
  - 02:00 AM → scraping completo de los 8 supermercados
  - 14:00 PM → segundo scraping para capturar cambios de precio de tarde
"""
import os
from celery import Celery
from celery.schedules import crontab

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "superapp",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["scheduler.tasks"],
)

celery_app.conf.update(
    task_serializer       = "json",
    result_serializer     = "json",
    accept_content        = ["json"],
    timezone              = "Europe/Madrid",
    enable_utc            = True,
    task_track_started    = True,
    task_acks_late        = True,         # no perder tareas si el worker cae
    worker_prefetch_multiplier = 1,       # un scraper a la vez por worker

    # ── Programación nocturna ──────────────────────────────
    beat_schedule={
        # Scraping principal — madrugada (precios de apertura)
        "scrape-all-supermarkets-night": {
            "task":     "scheduler.tasks.scrape_all_supermarkets",
            "schedule": crontab(hour=2, minute=0),
        },
        # Segundo scraping — tarde (algunos supers cambian precios a media jornada)
        "scrape-all-supermarkets-afternoon": {
            "task":     "scheduler.tasks.scrape_all_supermarkets",
            "schedule": crontab(hour=14, minute=0),
        },
    },
)
