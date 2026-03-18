"""
Scheduler — corre los scrapers cada 24hs automáticamente.
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from scraper.pedidosya import scrape_pedidosya
from scraper.rappi import scrape_rappi
from api.database import save_prices

logger = logging.getLogger(__name__)

BARRIOS = ["pocitos", "centro", "cordon", "punta_carretas", "ciudad_vieja", "palermo", "carrasco"]

async def run_scrapers():
    logger.info("🕷️ Iniciando scraping...")
    all_results = []

    for barrio in BARRIOS[:3]:  # Top 3 barrios por corrida para no saturar
        try:
            py_data  = await scrape_pedidosya(barrio)
            rp_data  = await scrape_rappi(barrio)
            all_results.extend(py_data)
            all_results.extend(rp_data)
        except Exception as e:
            logger.error(f"Error scraping {barrio}: {e}")

    if all_results:
        await save_prices(all_results)
        logger.info(f"✅ Guardados {len(all_results)} registros")
    else:
        logger.warning("⚠️ No se obtuvieron datos")


def start_scheduler():
    scheduler = AsyncIOScheduler()
    # Corre todos los días a las 6am hora Uruguay
    scheduler.add_job(
        run_scrapers,
        trigger="cron",
        hour=6,
        minute=0,
        timezone="America/Montevideo",
        id="daily_scrape",
        replace_existing=True,
    )
    scheduler.start()
    logger.info("⏰ Scheduler iniciado — scraping diario a las 6:00 AM UY")
    return scheduler
