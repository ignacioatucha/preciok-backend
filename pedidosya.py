"""
Scraper PedidosYa Uruguay — Playwright
Busca restaurantes y precios en Montevideo.
"""
import asyncio
import re
from playwright.async_api import async_playwright

BASE_URL = "https://www.pedidosya.com.uy"

CATEGORIES = {
    "burger":   "hamburguesas",
    "pizza":    "pizzas",
    "sushi":    "sushi",
    "pollo":    "pollo",
    "milanesa": "milanesas",
    "cafe":     "cafeterias",
}

async def scrape_pedidosya(barrio: str = "pocitos") -> list[dict]:
    results = []
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
            locale="es-UY",
            geolocation={"longitude": -56.1645, "latitude": -34.9011},
            permissions=["geolocation"],
        )
        page = await context.new_page()

        for cat_key, cat_slug in CATEGORIES.items():
            try:
                url = f"{BASE_URL}/restaurantes/{cat_slug}?address=Pocitos%2C+Montevideo"
                await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                await page.wait_for_timeout(3000)

                # Buscar cards de restaurantes
                restaurant_cards = await page.query_selector_all("[data-testid='restaurant-card'], .RestaurantCard, [class*='restaurantCard']")

                for card in restaurant_cards[:5]:  # Top 5 por categoría
                    try:
                        name_el = await card.query_selector("[class*='name'], [class*='title'], h3, h2")
                        delivery_el = await card.query_selector("[class*='delivery'], [class*='fee']")
                        
                        rest_name = await name_el.inner_text() if name_el else "Restaurante"
                        delivery_text = await delivery_el.inner_text() if delivery_el else "0"
                        
                        # Entrar al restaurante y buscar productos
                        link = await card.query_selector("a")
                        if not link:
                            continue
                        href = await link.get_attribute("href")
                        if not href:
                            continue
                        
                        rest_url = f"{BASE_URL}{href}" if href.startswith("/") else href
                        rest_page = await context.new_page()
                        await rest_page.goto(rest_url, wait_until="domcontentloaded", timeout=20000)
                        await rest_page.wait_for_timeout(2000)

                        products = await rest_page.query_selector_all("[data-testid='product-card'], [class*='productCard'], [class*='ProductCard']")
                        
                        for prod in products[:8]:  # Top 8 productos por restaurante
                            try:
                                prod_name_el = await prod.query_selector("[class*='name'], [class*='title'], h3, p")
                                price_el = await prod.query_selector("[class*='price'], [class*='Price']")
                                
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
                                        "pedidosya": price,
                                        "rappi": None,
                                        "delivery_py": delivery,
                                        "delivery_rappi": None,
                                        "barrio": barrio,
                                    })
                            except Exception:
                                continue
                        
                        await rest_page.close()
                    except Exception:
                        continue

            except Exception as e:
                print(f"[PY] Error en {cat_key}: {e}")
                continue

        await browser.close()
    
    print(f"[PY] Scraped {len(results)} productos")
    return results


def parse_price(text: str) -> float | None:
    if not text:
        return None
    # Extraer número de strings como "$1.290", "$ 890", "1290"
    clean = re.sub(r"[^\d,.]", "", text).replace(",", ".")
    parts = clean.split(".")
    if len(parts) > 2:
        # "1.290" → 1290
        clean = "".join(parts[:-1]) + "." + parts[-1] if parts[-1] else "".join(parts)
    try:
        val = float(clean)
        return val if val > 0 else None
    except Exception:
        return None


if __name__ == "__main__":
    async def main():
        data = await scrape_pedidosya()
        for d in data[:5]:
            print(d)
    asyncio.run(main())
