import asyncio
import asyncpg
import ssl


async def get_pg_pool_with_retry(dsn, retries=3, delay=2):
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    for attempt in range(1, retries + 1):
        try:
            pool = await asyncpg.create_pool(
                dsn=dsn, ssl=ssl_context, min_size=1, max_size=5, timeout=10
            )
            return pool
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < retries:
                await asyncio.sleep(delay)
            else:
                raise


async def main():
    pool = await get_pg_pool_with_retry(
        "postgresql://postgres:DRFzErwQSrXAqFUfwoWOGlconpKUYaLf@yamabiko.proxy.rlwy.net:24268/railway"
    )
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT * FROM weekly_hunt_schedule;")
        for row in rows:
            print(dict(row))
    await pool.close()


asyncio.run(main())
