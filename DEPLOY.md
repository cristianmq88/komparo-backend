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
3. Confirma. Render genera `SECRET_KEY`, crea la base de datos e inyecta
   `DATABASE_URL`.
4. Espera al despliegue y abre la URL pública en el móvil → ya tienes la app.
   - Android (Chrome): menú → «Añadir a pantalla de inicio» / «Instalar app».
   - iOS (Safari): Compartir → «Añadir a pantalla de inicio».

## Alternativa: Railway (Docker)

1. Crea un servicio **a partir del repo** (detecta el `Dockerfile`).
2. **+ New → Database → Add PostgreSQL** (inyecta `DATABASE_URL`).
3. En **Variables**, añade:

```
SECRET_KEY=una_cadena_larga_y_aleatoria
DATABASE_URL=${{Postgres.DATABASE_URL}}
```

   Genera la clave con:
   `python -c "import secrets; print(secrets.token_urlsafe(48))"`
4. **Settings → Networking → Generate Domain** y abre esa URL en el móvil.

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `DATABASE_URL` | Sí en producción | PostgreSQL. Sin ella usa SQLite local (se pierde al reiniciar). |
| `SECRET_KEY` | Sí en producción | Firma los tokens de sesión. Sin ella avisa en el arranque y usa una clave por defecto insegura. |
| `COOKIE_SECURE` | No | `false` solo para desarrollo en `http://` (ver abajo). |

## Probar en el móvil sin desplegar (misma WiFi)

Si tu teléfono está en la misma red que tu ordenador:

```bash
# Backend
COOKIE_SECURE=false uvicorn api.main:app --host 0.0.0.0 --port 8000

# Frontend (otra terminal)
cd frontend && npm install
npm run dev -- --host        # expone Vite en la red local
```

Abre en el móvil `http://IP-DE-TU-PC:5173` (verás la IP en la salida de Vite).

> **`COOKIE_SECURE=false` en local:** la sesión se guarda en una cookie HttpOnly
> que por defecto es `Secure` (solo viaja por HTTPS). En producción (Render/Railway,
> con HTTPS) esto es lo correcto y no hay que tocar nada. Pero en desarrollo local
> sobre `http://` el navegador descartaría la cookie y no podrías iniciar sesión.
