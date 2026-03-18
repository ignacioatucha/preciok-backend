"""
Scraper Rappi Uruguay — Playwright
Busca restaurantes y precios en Montevideo.
"""
import asyncio
import re
from playwright.async_api import async_playwright

BASE_URL = "https://www.rappi.com.uy"

CATEGORIES = {
    "burger":   "hamburguesas",
    "pizza":    "pizzas",
    "sushi":    "sushi",
    "pollo":    "pollo",
    "milanesa": "milanesas",
    "cafe":     "cafes",
}

async def scrape_rappi(barrio: str = "pocitos") -> list[dict]:
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-UY",
        )
        page = await context.new_page()

        for cat_key, cat_slug in CATEGORIES.items():
            try:
                url = f"{BASE_URL}/restaurantes/{cat_slug}"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(4000)

                # Rappi usa React — esperar que cargue el contenido
                await page.wait_for_selector("[class*='restaurant'], [class*='Restaurant'], [class*='store']", timeout=10000)

                cards = await page.query_selector_all("[class*='restaurant-card'], [class*='RestaurantCard'], [class*='storeCard']")

                for card in cards[:5]:
                    try:
                        name_el = await card.query_selector("h2, h3, [class*='name'], [class*='title']")
                        rest_name = await name_el.inner_text() if name_el else "Restaurante"

                        link = await card.query_selector("a")
                        if not link:
                            continue
                        href = await link.get_attribute("href")
                        if not href:
                            continue

                        rest_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                        rest_page = await context.new_page()
                        await rest_page.goto(rest_url, wait_until="domcontentloaded", timeout=20000)
                        await rest_page.wait_for_timeout(3000)

                        # Delivery fee
                        delivery_el = await rest_page.query_selector("[class*='delivery'], [class*='shipping']")
                        delivery_text = await delivery_el.inner_text() if delivery_el else "0"

                        products = await rest_page.query_selector_all("[class*='product'], [class*='Product'], [class*='item-card']")

                        for prod in products[:8]:
                            try:
                                prod_name_el = await prod.query_selector("h3, h4, [class*='name'], [class*='title']")
                                price_el = await prod.query_selector("[class*='price'], [class*='Price'], span[class*='value']")

                                prod_name = await prod_name_el.inner_text() if prod_name_el else None
                                price_text = await price_el.inner_text() if price_el else None

                                if not prod_name or not price_text:
                                    continue

                                price = parse_price(price_text)
                                delivery = parse_price(delivery_text)

                                if price and price > 0:
                                    results.append({
                                        "restaurant": rest_name.strip(),
                                        "name": prod_name.strip(),
                                        "category": cat_key,
                                        "pedidosya": None,
                                        "rappi": price,
                                        "delivery_py": None,
                                        "delivery_rappi": delivery,
                                        "barrio": barrio,
                                    })
                            except Exception:
                                continue

                        await rest_page.close()
                    except Exception:
                        continue

            except Exception as e:
                print(f"[Rappi] Error en {cat_key}: {e}")
                continue

        await browser.close()

    print(f"[Rappi] Scraped {len(results)} productos")
    return results


def parse_price(text: str) -> float | None:
    if not text:
        return None
    clean = re.sub(r"[^\d,.]", "", text).replace(",", ".")
    parts = clean.split(".")
    if len(parts) > 2:
        clean = "".join(parts[:-1]) + "." + parts[-1] if parts[-1] else "".join(parts)
    try:
        val = float(clean)
        return val if val > 0 else None
    except Exception:
        return None


if __name__ == "__main__":
    async def main():
        data = await scrape_rappi()
        for d in data[:5]:
            print(d)
    asyncio.run(main())
