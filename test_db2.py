import asyncpg
import ssl
import asyncio


async def get_pg_pool():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    pool = await asyncpg.create_pool(
        dsn="postgresql://postgres:DRFzErwQSrXAqFUfwoWOGlconpKUYaLf@yamabiko.proxy.rlwy.net:24268/railway",
        ssl=ssl_context,
        timeout=10,  # increase timeout if needed
        min_size=1,
        max_size=5,
    )
    return pool


async def test_pool():
    pool = await get_pg_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM weekly_hunt_schedule;")
        for row in rows:
            print(dict(row))
    await pool.close()


asyncio.run(test_pool())
