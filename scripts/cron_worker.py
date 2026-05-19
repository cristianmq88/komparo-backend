"""
Worker que se ejecuta diariamente en Railway para actualizar precios.

Configuración Railway:
  Cron schedule: 0 4 * * *
  Command:       python -m scripts.cron_worker
"""
import sys

from scrapers.run_scrapers import main

if __name__ == "__main__":
    sys.exit(main(sys.argv))
