# Desplegar Komparo (verlo en el móvil)

Komparo se despliega como **un único servicio**: el backend FastAPI sirve además
la web ya compilada. Así obtienes **una sola URL** que puedes abrir en el móvil e
incluso «instalar» como app (PWA).

## Cómo funciona

El `Dockerfile` tiene dos etapas:
1. Compila la web (`frontend/` → `frontend/dist`) con `VITE_API_BASE=""`, de modo
   que la web llama a la API en el mismo origen.
2. Levanta FastAPI, que sirve la API y, en `/`, la web compilada.

## Opción recomendada: Render en un clic (Blueprint)

El repo incluye `render.yaml`, que crea el servicio web + PostgreSQL y configura
las variables automáticamente.

1. Sube este repo a GitHub.
2. En [Render](https://render.com): **New → Blueprint** y conecta el repo.
3. Confirma. Render genera `SECRET_KEY` y `ADMIN_TOKEN`, crea la base de datos e
   inyecta `DATABASE_URL`.
4. Espera al despliegue y abre la URL pública en el móvil → ya tienes la app.
   - Android (Chrome): menú → «Añadir a pantalla de inicio» / «Instalar app».
   - iOS (Safari): Compartir → «Añadir a pantalla de inicio».

## Alternativa: Railway u otro (Docker manual)

1. Crea un servicio **a partir del repo** (detecta el `Dockerfile`).
2. Añade **PostgreSQL** (inyecta `DATABASE_URL`).
3. Configura las variables: `SECRET_KEY` y `ADMIN_TOKEN` (cadenas largas
   aleatorias). Opcionales: `SCRAPE_HOUR`, `PRODUCTS_PER_CATEGORY`.

## Precios reales: scrapeo automático

El scrapeo está **integrado y es automático** (planificador APScheduler):

- **Al arrancar**, si la base de datos está vacía, lanza un poblado inicial.
- **Cada día a las 04:00 UTC** (configurable con `SCRAPE_HOUR`) actualiza precios.

No necesitas hacer nada manual. Variables relacionadas:

| Variable | Por defecto | Descripción |
|----------|-------------|-------------|
| `ENABLE_SCHEDULER` | `true` | Activa/desactiva el planificador |
| `SCRAPE_ON_STARTUP` | `true` | Pobla al arrancar si está vacío |
| `SCRAPE_HOUR` | `4` | Hora UTC de la ejecución diaria |
| `PRODUCTS_PER_CATEGORY` | `30` | Productos por categoría y súper |

### Lanzar scrapers manualmente (opcional)

```bash
curl -X POST "https://TU-URL/admin/scrapers/run" -H "X-Admin-Token: TU_ADMIN_TOKEN"
curl -X POST "https://TU-URL/admin/scrapers/run?supermarket=mercadona" -H "X-Admin-Token: TU_ADMIN_TOKEN"
curl "https://TU-URL/admin/scrapers/status"
```

> ⚠️ **Importante sobre el scrapeo:** los scrapers usan las APIs internas de cada
> supermercado (Mercadona, Carrefour, Dia, Alcampo). Estas pueden cambiar su
> estructura o bloquear peticiones en cualquier momento; es la parte más frágil del
> sistema y puede requerir mantenimiento o un proxy anti-bloqueo (ScraperAPI,
> BrightData…). La app está preparada para que, en cuanto un scraper devuelva datos,
> aparezcan automáticamente; si un súper deja de funcionar, los demás siguen.

## Probar en el móvil sin desplegar (misma WiFi)

Si tu teléfono está en la misma red que tu ordenador:

```bash
# Backend
uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (otra terminal)
cd frontend && npm install
npm run dev -- --host        # expone Vite en la red local
```

Abre en el móvil `http://IP-DE-TU-PC:5173` (verás la IP en la salida de Vite).
