# ✅ Guía rápida: poner Komparo en producción (gratis)

Marca cada casilla según avances. Tiempo estimado: ~15 minutos.
La guía detallada está en [DEPLOY.md](DEPLOY.md).

## 1. Railway — crear el proyecto
- [ ] Entrar en https://railway.app → **Login with GitHub**
- [ ] **New Project** → **Deploy from GitHub repo** → elegir `komparo-backend`
- [ ] Esperar a que termine el primer build

## 2. Railway — base de datos
- [ ] **+ New** → **Database** → **Add PostgreSQL**
- [ ] Comprobar que aparece la caja **Postgres**

## 3. Railway — variables
- [ ] Generar la clave:
      `python -c "import secrets; print(secrets.token_urlsafe(48))"`
- [ ] Entrar en la caja de la app → pestaña **Variables** → **Raw Editor**
- [ ] Pegar (con tu clave):
      ```
      SECRET_KEY=tu_cadena_generada
      DATABASE_URL=${{Postgres.DATABASE_URL}}
      ```
- [ ] Guardar y esperar el redespliegue (verde / "Success")

## 4. Railway — dominio público
- [ ] Caja de la app → **Settings** → **Networking** → **Generate Domain**
- [ ] Guardar la URL (será la dirección de tu app)

## 5. Comprobar
- [ ] Abrir `https://TU-URL/` → se ve la pantalla de Komparo
- [ ] Abrir `https://TU-URL/health` → `{"status":"healthy"}`

## 6. Móvil 📱
- [ ] Abrir `https://TU-URL/` en el móvil
- [ ] Registrarse
- [ ] Instalar: Android (Chrome ⋮ → *Añadir a pantalla de inicio*) /
      iPhone (Safari, Compartir → *Añadir a pantalla de inicio*)

## Si algo falla
| Síntoma | Qué mirar |
|---------|-----------|
| La URL no carga | Último deploy en verde en Railway; si no, **Deploy** de nuevo |
| No puedo iniciar sesión | Que la URL sea `https://` (la cookie de sesión es Secure) |
| "DATABASE_URL not found" | Que la base de datos se llame **Postgres** (paso 2) |
