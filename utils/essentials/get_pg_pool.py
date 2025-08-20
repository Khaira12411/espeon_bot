import os
import ssl
import asyncpg
from utils.loggers.espeon_log import espeon_log, EspeonContext  # Using Espeon logs


async def get_pg_pool():
    internal_url = os.getenv("DATABASE_URL")
    public_url = os.getenv("DATABASE_PUBLIC_URL")

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

    # 🧸 Try public URL fallback
    try:
        pool = await asyncpg.create_pool(dsn=public_url, ssl=ssl_context)
        espeon_log(
            "db",
            "Connected to Postgres via public URL!",
            context=EspeonContext.STRAYMONS,
        )
        return pool
    except Exception as e:
        espeon_log(
            "warn",
            f"Public URL failed to connect: {e}",
            context=EspeonContext.STRAYMONS,
            exc=e,
        )

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
