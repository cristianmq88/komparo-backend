"""
Planificador de scrapers integrado en la app.

Cuando la app arranca:
  - Programa una ejecución diaria de todos los scrapers (por defecto 04:00 UTC).
  - Si la base de datos de precios está vacía, lanza una ejecución inicial
    para poblarla cuanto antes (en segundo plano, sin bloquear el arranque).

Todo es configurable por variables de entorno:
  ENABLE_SCHEDULER     "1"/"true" para activar (por defecto activado)
  SCRAPE_HOUR          hora UTC de la ejecución diaria (por defecto 4)
  SCRAPE_ON_STARTUP    "1"/"true" para poblar al arrancar si está vacío (def. activado)
  PRODUCTS_PER_CATEGORY  productos por categoría y súper (por defecto 30)
"""
import logging
import os

logger = logging.getLogger(__name__)

_scheduler = None


def _env_flag(name: str, default: bool) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _products_per_category() -> int:
    try:
        return int(os.getenv("PRODUCTS_PER_CATEGORY", "30"))
    except ValueError:
        return 30


def _has_prices() -> bool:
    """True si ya hay algún precio en la base de datos."""
    from db.database import SessionLocal
    from db.models_prices import CurrentPrice

    db = SessionLocal()
    try:
        return db.query(CurrentPrice.id).first() is not None
    except Exception as e:  # tabla aún no creada, etc.
        logger.warning(f"No se pudo comprobar precios existentes: {e}")
        return True  # ante la duda, no relanzar
    finally:
        db.close()


def _run_all_job():
    """Ejecuta todos los scrapers (usado por el planificador)."""
    from scrapers.run_scrapers import run_all

    logger.info("⏰ Ejecución programada de scrapers")
    try:
        run_all(products_per_category=_products_per_category())
    except Exception as e:  # pragma: no cover
        logger.error(f"Fallo en la ejecución programada: {e}", exc_info=True)


def _initial_population_job():
    """Pobla la BD la primera vez, solo si está vacía."""
    if _has_prices():
        logger.info("ℹ️ Ya hay precios en la BD; no se relanza el poblado inicial")
        return
    logger.info("🌱 Base de datos vacía: lanzando poblado inicial de precios")
    _run_all_job()


def start_scheduler():
    """Arranca el planificador en segundo plano. Idempotente."""
    global _scheduler

    if not _env_flag("ENABLE_SCHEDULER", True):
        logger.info("🛑 Planificador desactivado (ENABLE_SCHEDULER=false)")
        return

    if _scheduler is not None:
        return

    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger
    except ImportError:
        logger.warning("⚠️ APScheduler no instalado; sin scrapeo automático")
        return

    from datetime import datetime, timedelta

    scheduler = BackgroundScheduler(timezone="UTC", daemon=True)

    hour = 4
    try:
        hour = int(os.getenv("SCRAPE_HOUR", "4"))
    except ValueError:
        pass

    # Ejecución diaria
    scheduler.add_job(
        _run_all_job,
        CronTrigger(hour=hour, minute=0),
        id="daily_scrape",
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info(f"🗓️ Scrapeo diario programado a las {hour:02d}:00 UTC")

    # Poblado inicial si está vacío (poco después de arrancar)
    if _env_flag("SCRAPE_ON_STARTUP", True):
        scheduler.add_job(
            _initial_population_job,
            DateTrigger(run_date=datetime.utcnow() + timedelta(seconds=20)),
            id="initial_population",
            replace_existing=True,
            max_instances=1,
        )
        logger.info("🌱 Poblado inicial programado (si la BD está vacía)")

    scheduler.start()
    _scheduler = scheduler
