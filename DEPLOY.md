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
> sistema. La app está preparada para que, en cuanto un scraper devuelva datos,
> aparezcan automáticamente; si un súper deja de funcionar, los demás siguen.

## Proxy anti-bloqueo (recomendado en producción)

Para reducir los bloqueos por IP, los scrapers pueden enrutar las peticiones a
través de un **proxy rotativo** y además rotan el User-Agent automáticamente. Se
activa con variables de entorno; si no configuras nada, van directos.

Elige **un** modo:

**1) ScraperAPI** (el más sencillo; rota la IP en su servidor):

| Variable | Ejemplo | Descripción |
|----------|---------|-------------|
| `SCRAPERAPI_KEY` | `abc123...` | Tu API key de scraperapi.com |
| `SCRAPERAPI_COUNTRY` | `es` | País de salida (opcional) |
| `SCRAPERAPI_RENDER` | `false` | `true` ejecuta JS (gasta más créditos) |

**2) Gateway único** (BrightData, Smartproxy, Oxylabs…):

| Variable | Ejemplo |
|----------|---------|
| `SCRAPER_PROXY_URL` | `http://usuario:pass@gateway.proveedor.com:22225` |

**3) Lista de proxies con rotación local** (round-robin):

| Variable | Ejemplo |
|----------|---------|
| `SCRAPER_PROXIES` | `http://u:p@ip1:8000,http://u:p@ip2:8000` |

Otras: `SCRAPER_PROXY_VERIFY=false` desactiva la verificación TLS (se desactiva
sola con ScraperAPI). Comprueba si está activo en `GET /admin/scrapers/status`
(campo `proxy.enabled`).

> Estos servicios son de pago. El proxy es **opcional**: la app funciona sin él,
> pero con un volumen alto de scrapeo es muy recomendable para evitar bloqueos.

## Respaldo: scrapeo desde GitHub Actions

El repo incluye `.github/workflows/scrape.yml`, que ejecuta los scrapers desde los
runners de GitHub (internet abierto) y escribe en la BD de producción. Es un
respaldo del planificador interno, útil si el servicio web se duerme.

> ⏸️ **La ejecución diaria está desactivada.** Sin el secreto `DATABASE_URL` el
> workflow fallaba cada mañana, así que el disparador `schedule` está comentado.
> De momento solo se puede lanzar a mano. Para reactivar el diario: configura el
> secreto y descomenta las dos líneas de `schedule` en el workflow.

Para activarlo, añade en **GitHub → Settings → Secrets and variables → Actions**:

| Secreto | Valor |
|---------|-------|
| `DATABASE_URL` | conexión **pública** del Postgres de Railway (Postgres → Connect → Public Network) |
| `SCRAPERAPI_KEY` | (opcional) clave del proxy anti-bloqueo |

Puedes lanzarlo a mano desde la pestaña **Actions → Scrapeo de precios → Run workflow**.

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
> sobre `http://` el navegador descartaría la cookie y no podrías iniciar sesión, así
> que ahí se desactiva con `COOKIE_SECURE=false`.
