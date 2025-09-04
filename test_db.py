import asyncpg
import ssl
import asyncio


async def test_query():
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    conn = await asyncpg.connect(
        dsn="postgresql://postgres:DRFzErwQSrXAqFUfwoWOGlconpKUYaLf@yamabiko.proxy.rlwy.net:24268/railway",
        ssl=ssl_context,
    )

    # Run your query
    rows = await conn.fetch("SELECT * FROM weekly_hunt_schedule;")

    for row in rows:
        print(dict(row))  # convert row to dict for readability

    await conn.close()


asyncio.run(test_query())
