# PreciOK Backend — Fase 2

API REST + Scraper automático de precios de PedidosYa y Rappi en Montevideo.

## Stack
- **FastAPI** — API REST
- **Playwright** — Web scraping
- **SQLite** — Base de datos
- **APScheduler** — Scraping automático cada 24hs

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/api/deals` | Precios más recientes |
| GET | `/api/deals?category=burger` | Filtrar por categoría |
| GET | `/api/deals?barrio=pocitos` | Filtrar por barrio |
| GET | `/api/history?name=X&restaurant=Y` | Historial de un plato |
| GET | `/api/stats` | Stats generales |
| POST | `/api/scrape` | Forzar scraping manual |

## Deploy en Railway

1. Subí este repositorio a GitHub
2. En railway.app → New Project → Deploy from GitHub
3. Seleccioná este repo
4. Railway detecta el `Procfile` automáticamente
5. Esperá que termine el build (~3 minutos)
6. Copiá la URL pública que genera Railway

## Conectar con el frontend

En `preciok.html`, reemplazá la línea:
```js
const deals = [ /* datos simulados */ ]
```
por:
```js
const API_URL = "https://TU-URL.railway.app";
// Al cargar la página:
const resp = await fetch(`${API_URL}/api/deals`);
const { deals } = await resp.json();
```
