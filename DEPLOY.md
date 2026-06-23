# Desplegar Komparo (verlo en el móvil)

Komparo se despliega como **un único servicio**: el backend FastAPI sirve además
la web ya compilada. Así obtienes **una sola URL** que puedes abrir en el móvil e
incluso «instalar» como app (PWA).

## Cómo funciona

El `Dockerfile` tiene dos etapas:
1. Compila la web (`frontend/` → `frontend/dist`) con `VITE_API_BASE=""`, de modo
   que la web llama a la API en el mismo origen.
2. Levanta FastAPI, que sirve la API y, en `/`, la web compilada.

## Opción recomendada: Railway / Render (Docker)

1. Sube este repo a GitHub (rama `main` o la que uses).
2. Crea un nuevo servicio en [Railway](https://railway.app) o
   [Render](https://render.com) **a partir del repo** (detecta el `Dockerfile`).
3. Añade una base de datos **PostgreSQL** (botón "Add PostgreSQL"). La plataforma
   inyecta `DATABASE_URL` automáticamente.
4. Configura estas variables de entorno:

   | Variable        | Valor                                              |
   |-----------------|----------------------------------------------------|
   | `SECRET_KEY`    | una cadena larga y aleatoria (firma de los JWT)    |
   | `ADMIN_TOKEN`   | un token secreto para lanzar los scrapers          |
   | `DATABASE_URL`  | la proporciona la plataforma (PostgreSQL)          |

5. Despliega. Abre la URL pública en el móvil → ya tienes la app.
   - En Android (Chrome): menú → «Añadir a pantalla de inicio» / «Instalar app».
   - En iOS (Safari): Compartir → «Añadir a pantalla de inicio».

## Poblar precios reales

Los precios se obtienen con los scrapers, que **necesitan internet abierto** (no
funcionan en sandboxes con proxy restringido). Una vez desplegado:

```bash
# Lanzar todos los scrapers
curl -X POST "https://TU-URL/admin/scrapers/run" \
  -H "X-Admin-Token: TU_ADMIN_TOKEN"

# Solo uno
curl -X POST "https://TU-URL/admin/scrapers/run?supermarket=mercadona" \
  -H "X-Admin-Token: TU_ADMIN_TOKEN"

# Ver estado
curl "https://TU-URL/admin/scrapers/status"
```

> Nota: los scrapers dependen de las webs/APIs internas de cada supermercado, que
> pueden cambiar o bloquear peticiones. Es la parte más frágil del sistema y puede
> requerir mantenimiento o un proxy anti-bloqueo.

Para automatizarlo a diario, programa ese `curl` como cron (Railway Cron, GitHub
Actions, etc.) o usa `scripts/cron_worker.py`.

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
