import aiosqlite
import os

DB_PATH = os.getenv("DB_PATH", "preciok.db")

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS precios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                restaurant TEXT NOT NULL,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                pedidosya REAL,
                rappi REAL,
                delivery_py REAL,
                delivery_rappi REAL,
                barrio TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_name ON precios(name);
        """)
        await db.execute("""
            CREATE INDEX IF NOT EXISTS idx_scraped ON precios(scraped_at);
        """)
        await db.commit()

async def save_prices(items: list[dict]):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany("""
            INSERT INTO precios (restaurant, name, category, pedidosya, rappi, delivery_py, delivery_rappi, barrio)
            VALUES (:restaurant, :name, :category, :pedidosya, :rappi, :delivery_py, :delivery_rappi, :barrio)
        """, items)
        await db.commit()

async def get_latest_prices(category: str = None, barrio: str = None, q: str = None):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        # Traer solo los precios más recientes por plato (último scraping)
        query = """
            SELECT p.* FROM precios p
            INNER JOIN (
                SELECT name, restaurant, MAX(scraped_at) as last
                FROM precios GROUP BY name, restaurant
            ) latest ON p.name = latest.name 
                AND p.restaurant = latest.restaurant 
                AND p.scraped_at = latest.last
            WHERE 1=1
        """
        params = []
        if category and category != "all":
            query += " AND p.category = ?"
            params.append(category)
        if barrio and barrio != "all":
            query += " AND (p.barrio = ? OR p.barrio IS NULL)"
            params.append(barrio)
        if q:
            query += " AND (p.name LIKE ? OR p.restaurant LIKE ?)"
            params.extend([f"%{q}%", f"%{q}%"])
        query += " ORDER BY ABS(COALESCE(p.pedidosya,0) - COALESCE(p.rappi,0)) DESC LIMIT 100"
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]

async def get_price_history(name: str, restaurant: str):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("""
            SELECT pedidosya, rappi, delivery_py, delivery_rappi, scraped_at
            FROM precios WHERE name = ? AND restaurant = ?
            ORDER BY scraped_at DESC LIMIT 30
        """, (name, restaurant)) as cursor:
            rows = await cursor.fetchall()
            return [dict(row) for row in rows]
