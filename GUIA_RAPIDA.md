# ✅ Guía rápida: poner Komparo en producción (gratis)

Marca cada casilla según avances. Tiempo estimado: ~20 minutos.
La guía detallada está en [DEPLOY.md](DEPLOY.md).

## 1. GitHub — fusionar el código
- [ ] Abrir https://github.com/cristianmq88/komparo-backend/pull/2
- [ ] Pulsar **Merge pull request** → **Confirm merge**

## 2. Railway — crear el proyecto
- [ ] Entrar en https://railway.app → **Login with GitHub**
- [ ] **New Project** → **Deploy from GitHub repo** → elegir `komparo-backend`
- [ ] Esperar a que termine el primer build

## 3. Railway — base de datos
- [ ] **+ New** → **Database** → **Add PostgreSQL**
- [ ] Comprobar que aparece la caja **Postgres**

## 4. Railway — variables
- [ ] Entrar en la caja de la app → pestaña **Variables** → **Raw Editor**
- [ ] Pegar el bloque de variables (SECRET_KEY, ADMIN_TOKEN, DATABASE_URL,
      ENABLE_SCHEDULER, SCRAPE_ON_STARTUP, ENABLE_DAILY_SCRAPE=false,
      PRODUCTS_PER_CATEGORY) — *usa tus valores secretos, no los subas a Git*
- [ ] Guardar y esperar el redespliegue (verde / "Success")

## 5. Railway — dominio público
- [ ] Caja de la app → **Settings** → **Networking** → **Generate Domain**
- [ ] Guardar la URL (será la dirección de tu app)

## 6. Comprobar
- [ ] Abrir `https://TU-URL/` → se ve la pantalla de Komparo
- [ ] Abrir `https://TU-URL/health` → `{"status":"healthy"}`
- [ ] Abrir `https://TU-URL/admin/scrapers/status` → ver `products_in_db`

## 7. GitHub — refresco diario gratis
- [ ] En Railway: caja **Postgres** → **Connect** → copiar la `DATABASE_URL`
      **pública** (contiene `proxy.rlwy.net`)
- [ ] En GitHub: **Settings → Secrets and variables → Actions →
      New repository secret** → Name: `DATABASE_URL` → pegar → **Add secret**
- [ ] Pestaña **Actions** → workflow **"Scrapeo de precios (respaldo)"** →
      **Run workflow** (primera carga manual)
- [ ] Esperar el ✔️ verde y recargar la app: ya hay precios

## 8. Móvil 📱
- [ ] Abrir `https://TU-URL/` en el móvil
- [ ] Registrarse
- [ ] Instalar: Android (Chrome ⋮ → *Añadir a pantalla de inicio*) /
      iPhone (Safari, Compartir → *Añadir a pantalla de inicio*)

## Si algo falla
| Síntoma | Qué mirar |
|---------|-----------|
| La URL no carga | Último deploy en verde en Railway; si no, **Deploy** de nuevo |
| Sin precios (`products_in_db: 0`) | Lanzar el workflow del paso 7; ver la tabla de estado por súper |
| Action con ✗ rojo | El secreto `DATABASE_URL` debe ser la conexión **pública** |
| Un súper siempre a 0 | Te está bloqueando → valorar proxy de pago (`SCRAPERAPI_KEY`) |
