"""
Scheduler — corre los scrapers cada 24hs automáticamente.
"""
import asyncio
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import pedidosya
import rappi
import database

logger = logging.getLogger(__name__)

BARRIOS = ["pocitos", "centro", "cordon", "punta_carretas", "ciudad_vieja"]

async def run_scrapers():
    logger.info("🕷️ Iniciando scraping...")
    all_results = []
    for barrio in BARRIOS[:3]:
        try:
            py_data = await pedidosya.scrape_pedidosya(barrio)
            rp_data = await rappi.scrape_rappi(barrio)
            all_results.extend(py_data)
            all_results.extend(rp_data)
        except Exception as e:
            logger.error(f"Error scraping {barrio}: {e}")
    if all_results:
        await database.save_prices(all_results)
        logger.info(f"✅ Guardados {len(all_results)} registros")
    else:
        logger.warning("⚠️ No se obtuvieron datos")


def start_scheduler():
    scheduler = AsyncIOScheduler()
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
