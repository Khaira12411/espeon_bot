import os
import ssl
import asyncpg
import asyncio
from utils.loggers.espeon_log import espeon_log, EspeonContext
from dotenv import load_dotenv

load_dotenv()


async def get_pg_pool():
    internal_url = os.getenv("DATABASE_URL")
    public_url = (
        os.getenv("DATABASE_PUBLIC_URL")
        or "postgresql://postgres:DRFzErwQSrXAqFUfwoWOGlconpKUYaLf@yamabiko.proxy.rlwy.net:24268/railway"
    )

    # 💖 SSL context for cozy vibes
    ssl_context = ssl.create_default_context()
    ssl_context.check_hostname = False
    ssl_context.verify_mode = ssl.CERT_NONE

    # 🌸 Try internal URL
    try:
        pool = await asyncpg.create_pool(dsn=internal_url, ssl=ssl_context)
        espeon_log(
            "db",
            "Connected to Postgres via internal URL!",
            context=EspeonContext.STRAYMONS,
        )
        return pool
    except Exception as e:
        espeon_log(
            "warn",
            f"Internal URL failed to connect: {e}",
            context=EspeonContext.STRAYMONS,
            exc=e,
        )

    # 🧸 Try public URL fallback with retries
    max_attempts = 5
    for attempt in range(1, max_attempts + 1):
        try:
            pool = await asyncpg.create_pool(dsn=public_url, ssl=ssl_context)
            espeon_log(
                "db",
                f"Connected to Postgres via public URL on attempt {attempt}!",
                context=EspeonContext.STRAYMONS,
            )
            return pool
        except Exception as e:
            espeon_log(
                "warn",
                f"Attempt {attempt} to connect via public URL failed: {e}",
                context=EspeonContext.STRAYMONS,
                exc=e,
            )
            await asyncio.sleep(2)  # short delay before retrying

    # 🌷 Both attempts failed
    espeon_log(
        "critical",
        "Could not connect to either internal or public Postgres database.",
        context=EspeonContext.STRAYMONS,
        include_trace=True,
    )
    raise ConnectionError(
        "💖 Could not connect to either internal or public Postgres database. Sending cozy vibes!"
    )
