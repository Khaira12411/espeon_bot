import glob
import logging
import os
import random
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from config.current_setup import *
from utils.cache.centralized_cache_loader import load_all_caches
from utils.cache.market_alert_cache import load_market_alert_cache
from utils.essentials.get_pg_pool import get_pg_pool
from utils.loggers.espeon_log import espeon_log  # Using Espeon logs
from utils.loggers.rate_limit_logger import setup_rate_limit_logging

# ——————————————————————————————————————————————————————————————
# Suppress discord.py logs (must be set BEFORE imports)
# ——————————————————————————————————————————————————————————————
logging.basicConfig(level=logging.CRITICAL)
for logger_name in [
    "discord",
    "discord.gateway",
    "discord.http",
    "discord.voice_client",
    "asyncio",
]:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)
logging.getLogger("discord.client").setLevel(logging.CRITICAL)

# ——————————————————————————————————————————————————————————————
# Bot Setup
# ——————————————————————————————————————————————————————————————
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
setup_rate_limit_logging(bot)

ASIA_MANILA = ZoneInfo("Asia/Manila")

# 💜 Status Messages
MORNING_STATUSES = [
    (discord.ActivityType.playing, "gazing at the morning haze 🌄💜"),
    (discord.ActivityType.playing, "tracing sunlit streams ☀️🪻"),
    (discord.ActivityType.listening, "whispers of the wind 🌀💜"),
    (discord.ActivityType.listening, "birds singing in the dawn 🎶💜"),
    (discord.ActivityType.watching, "the sunrise shimmer ✨🌅"),
    (discord.ActivityType.watching, "dew sparkling on petals 🌸💜"),
]

NIGHT_STATUSES = [
    (discord.ActivityType.playing, "strolling under the moonlight 🌙💫"),
    (discord.ActivityType.playing, "shadowed paths alongside Umbreon 🌌🖤"),
    (discord.ActivityType.listening, "to distant star hums 🎶🌌"),
    (discord.ActivityType.listening, "to night breezes rustling Umbreon’s fur 🍃🖤"),
    (discord.ActivityType.watching, "the cosmos unfold ✨🌃"),
    (discord.ActivityType.watching, "Umbreon’s eyes glimmering in the dark 🌙🩷"),
]

DEFAULT_STATUSES = [
    (discord.ActivityType.playing, "floating in silent thought 💜🌸"),
    (
        discord.ActivityType.playing,
        "leaping between light and shadow with Umbreon ✨🖤",
    ),
    (discord.ActivityType.listening, "to psychic echoes 🧠💜"),
    (
        discord.ActivityType.listening,
        "to whispers of the night shared with Umbreon 🌌🖤",
    ),
    (discord.ActivityType.watching, "twilight light and shadow 🌌💜"),
    (discord.ActivityType.watching, "stars shimmering as Umbreon prowls ✨🩷"),
]


# 💜 Status Rotator
def pick_status_tuple():
    """Return a random status based on current time."""
    now = datetime.now(ASIA_MANILA)
    if 6 <= now.hour < 18:
        pool = MORNING_STATUSES
    else:
        pool = NIGHT_STATUSES
    return random.choice(pool)


# 💜 Status Rotator Task
@tasks.loop(minutes=5)
async def status_rotator():
    activity_type, message = pick_status_tuple()
    espeon_log("ready", f"Switching status → {activity_type.name}: {message}")
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


"""# 💜 Market Alert Cache Refresh Task
@tasks.loop(hours=1)
async def refresh_market_alert_cache():
    await load_market_alert_cache(bot)
    espeon_log("ready", "🔄 Market alert cache refreshed")
"""

# ────────────────────────────────────────────
#       💜 Hourly Cache Refresh Loop 💜
# ─────────────────────────────────────────────
@tasks.loop(hours=1)
async def refresh_all_caches():
    await load_all_caches(bot)
    espeon_log("ready", "🔄 All caches refreshed (Market Alerts + Mr. Weakness)")


# 💜 Global Error Handler
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        return
    espeon_log(
        "error",
        f"Command error: {error}",
        context=ctx.cog if ctx.cog else None,
        include_trace=True,
    )


# 💜 on_ready Event
@bot.event
async def on_ready():
    espeon_log("ready", f"EspeonBot awake as {bot.user}")

    # 💜 Syncing slash commands
    await bot.tree.sync()
    espeon_log("ready", "Slash commands synced with Discord successfully!")

    if hasattr(bot, "pg_pool"):
        espeon_log("db", "PostgreSQL connection pool is ready!")
    else:
        espeon_log("warn", "pg_pool is not attached!")

    if not status_rotator.is_running():
        espeon_log("ready", "Starting EspeonBot status loop...")
        status_rotator.start()

    # Set initial status
    activity_type, message = pick_status_tuple()
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )

    # 💜 Load all caches on startup (Market Alerts + Mr. Weakness)
    refresh_all_caches.start()
    
    """try:
        await load_all_caches(bot)
        espeon_log("ready", "✅ All caches loaded (Market Alerts + Mr. Weakness)")
    except Exception as e:
        espeon_log("error", f"Failed to load caches: {e}", include_trace=True)"""

    #


# 💜 Loading Cogs & Database
@bot.event
async def setup_hook():
    espeon_log("ready", "Setting up database and loading cogs...")
    try:
        pg_pool = await get_pg_pool()
        async with pg_pool.acquire() as conn:
            version = await conn.fetchval("SELECT version();")
            espeon_log("db", f"Connected to Postgres (v{version})")
        bot.pg_pool = pg_pool
    except Exception as e:
        espeon_log("critical", f"Postgres connection failed: {e}", include_trace=True)

    loaded_count = 0
    for cog_path in glob.glob("cogs/**/*.py", recursive=True):
        relative_path = os.path.relpath(cog_path, "cogs")
        module_name = relative_path[:-3].replace(os.sep, ".")
        cog_name = f"cogs.{module_name}"
        try:
            await bot.load_extension(cog_name)
            loaded_count += 1
        except Exception as e:
            espeon_log("error", f"Failed to load {cog_name}: {e}", include_trace=True)

    espeon_log("ready", f"All cogs loaded successfully: {loaded_count}")

    # 💜 Syncing guild slash commands
    try:
        await bot.tree.sync(guild=discord.Object(id=ACTIVE_GUILD_ID))
        espeon_log("ready", "Slash commands synced to Active Guild!")
    except Exception as e:
        espeon_log("error", f"Guild sync failed: {e}", include_trace=True)


# 💜 Starting Bot
if __name__ == "__main__":
    load_dotenv()
    espeon_log("ready", "EspeonBot is starting...")

    while True:
        try:
            bot.run(os.getenv("DISCORD_TOKEN"))
        except Exception as e:
            espeon_log("error", f"Bot crashed: {e}", include_trace=True)
            espeon_log("ready", "Restarting EspeonBot in 5 seconds...")
            time.sleep(5)
