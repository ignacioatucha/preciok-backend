"""
PreciOK API — FastAPI
Endpoints para el frontend comparador de precios.
"""
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from api.database import init_db, get_latest_prices, get_price_history
from api.scheduler import start_scheduler, run_scrapers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    await init_db()
    logger.info("✅ Base de datos inicializada")
    scheduler = start_scheduler()
    # Primera corrida al iniciar si la BD está vacía
    prices = await get_latest_prices()
    if not prices:
        logger.info("🔄 BD vacía — corriendo scraping inicial...")
        await run_scrapers()
    yield
    # Shutdown
    scheduler.shutdown()


app = FastAPI(
    title="PreciOK API",
    description="Compará precios de delivery en Montevideo",
    version="2.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción cambiar por el dominio real
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    return {"status": "ok", "app": "PreciOK API v2"}


@app.get("/api/deals")
async def get_deals(
    category: str = Query(default="all"),
    barrio: str   = Query(default="all"),
    q: str        = Query(default=None),
):
    """
    Retorna los precios más recientes.
    El frontend los usa para reemplazar los datos simulados.
    """
    items = await get_latest_prices(category=category, barrio=barrio, q=q)

    # Formatear para que sea compatible con el array 'deals' del frontend
    deals = []
    for i, item in enumerate(items):
        py  = item.get("pedidosya")
        rp  = item.get("rappi")
        dpy = item.get("delivery_py") or 59
        drp = item.get("delivery_rappi") or 69

        deals.append({
            "id":         i + 1,
            "restaurant": item["restaurant"],
            "name":       item["name"],
            "pedidosya":  py,
            "rappi":      rp,
            "dPY":        dpy,
            "dRP":        drp,
            "cat":        item["category"],
            "barrios":    [item["barrio"]] if item.get("barrio") else [],
            "scraped_at": item.get("scraped_at"),
        })

    return {"deals": deals, "total": len(deals)}


@app.get("/api/history")
async def get_history(
    name:       str = Query(...),
    restaurant: str = Query(...),
):
    """Historial de precios de un plato específico (para el gráfico del modal)."""
    history = await get_price_history(name, restaurant)
    return {"history": history}


@app.post("/api/scrape")
async def trigger_scrape():
    """Forzar un scraping manual (útil para pruebas)."""
    await run_scrapers()
    return {"status": "ok", "message": "Scraping completado"}


@app.get("/api/stats")
async def get_stats():
    """Stats generales para el home."""
    all_items = await get_latest_prices()
    if not all_items:
        return {"total_dishes": 0, "avg_saving": 0, "max_diff": 0, "restaurants": 0}

    savings = []
    for item in all_items:
        py = item.get("pedidosya")
        rp = item.get("rappi")
        if py and rp:
            savings.append(abs(py - rp))

    restaurants = len(set(i["restaurant"] for i in all_items))

    return {
        "total_dishes":  len(all_items),
        "avg_saving":    round(sum(savings) / len(savings)) if savings else 0,
        "max_diff":      round(max(savings)) if savings else 0,
        "restaurants":   restaurants,
    }
