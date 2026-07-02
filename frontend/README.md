# Komparo · Web app

Frontend en **React + Vite** para el backend de Komparo (FastAPI). Permite
comparar precios de supermercados, gestionar cestas de la compra y convertir
recetas en listas.

## Funcionalidades

- 🔐 **Cuenta**: registro, inicio de sesión (JWT), edición de perfil, **cambio de
  contraseña** y **eliminación de cuenta** (RGPD)
- 🔍 **Búsqueda de precios reales** con imagen, marca y comparativa visual por súper
- 📊 **Ficha de producto**: precio en cada supermercado y enlaces de compra
- 🧺 **Cestas de la compra**: crear, añadir/quitar productos y eliminar
- 💰 **Comparar cesta** con **precios reales**, ranking y ahorro
- 🍳 **Recetas**: explorar por categoría y crear una cesta con sus ingredientes
- 📱 **PWA instalable** y diseño responsive (barra de navegación inferior en móvil)
- ⚖️ **Páginas legales**: privacidad, términos y cookies + banner de consentimiento

> Los precios reales los pueblan los scrapers del backend. Consulta
> [`../DEPLOY.md`](../DEPLOY.md) para desplegar y verlo en el móvil.

## Requisitos

- Node.js 18+ (probado con Node 22)
- El backend de Komparo corriendo (por defecto en `http://localhost:8000`)

## Puesta en marcha

```bash
cd frontend
npm install
cp .env.example .env   # ajusta VITE_API_URL si tu backend está en otra URL
npm run dev
```

La app queda en `http://localhost:5173`. En desarrollo, Vite hace proxy de
`/api/*` hacia el backend (`VITE_API_URL`), evitando problemas de CORS.

## Build de producción

```bash
npm run build      # genera dist/
npm run preview    # sirve dist/ localmente para probar
```

En producción puedes apuntar la app directamente al backend definiendo
`VITE_API_BASE` (URL absoluta) en lugar de usar el proxy. Por ejemplo:

```bash
VITE_API_BASE=https://api.komparo.example npm run build
```

## Estructura

```
src/
  api/client.js          Cliente HTTP de la API
  context/AuthContext    Estado de sesión (login/registro/logout)
  components/            Navbar, Layout, PriceBars, rutas protegidas…
  pages/                 Login, Register, Search, Lists, ListDetail,
                         Recipes, RecipeDetail
```
