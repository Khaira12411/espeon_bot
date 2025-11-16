import glob
import logging
import os
import random
import time
import tracemalloc
from datetime import datetime
from zoneinfo import ZoneInfo

import discord
from discord.ext import commands, tasks
from dotenv import load_dotenv

from config.current_setup import *
from utils.cache.centralized_cache_loader import load_all_caches
from utils.essentials.command_tracker import auto_log_new_commands
from utils.essentials.error_handler import on_app_command_error
from utils.essentials.get_pg_pool import get_pg_pool
from utils.essentials.role_checks import *
from utils.loggers.espeon_log import EspeonContext  # Using Espeon logs
from utils.loggers.espeon_log import espeon_log, set_espeon_bot
from utils.loggers.rate_limit_logger import setup_rate_limit_logging
from utils.listener_func.event_checklist_caught import processed_rare_catches
from utils.listener_func.market_alert import processed_market_feed_message_ids, processed_snipe_ids

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
# Suppress the noisy "Ignoring exception in autocomplete" messages
logging.getLogger("discord.app_commands.tree").setLevel(logging.CRITICAL)

tracemalloc.start()
# ——————————————————————————————————————————————————————————————
# 💜 Bot Setup
# ——————————————————————————————————————————————————————————————

# 🧩 Intents setup (what the bot can listen to)
intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True
intents.members = True

# 🐾 Create the bot instance
bot = commands.Bot(command_prefix="!", intents=intents)

# 💌 Tell the logger which bot instance to use
set_espeon_bot(bot)

# 🪻 Hook in rate-limit logging (keeps us safe from spammy APIs)
setup_rate_limit_logging(bot)

# Example: Print top memory usage after bot setup
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")

# print("[ Top 10 memory usage ]")
"""for stat in top_stats[:10]:
    print(stat)"""
# 🌸 Allowed guilds (keeps bot scoped to friendly homes only!)
ALLOWED_GUILD_IDS = {
    STRAYMONS_GUILD_ID,
    MEOW_SUMMIT_GUILD_ID,
    CC_GUILD_ID,
    STAFF_SERVER_GUILD_ID,
}


@bot.event
async def on_guild_join(guild):
    try:
        # Fetch Khy
        khy_user = await bot.fetch_user(KHY_USER_ID)

        # Fetch guild owner
        guild_owner = guild.owner or await bot.fetch_user(guild.owner_id)
        owner_name = guild_owner.name if guild_owner else "Unknown"
        owner_id = guild_owner.id if guild_owner else "Unknown"

        # ✅ DM Khy about the guild join
        try:
            await khy_user.send(
                f"Espeon joined a guild:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})"
            )
        except Exception:
            espeon_log(
                "warn",
                f"Could not DM Khy about guild join for {guild.name}.",
                context=EspeonContext.ESPEON,
            )

        # Check if guild is authorized
        if guild.id in ALLOWED_GUILD_IDS:
            espeon_log(
                "ready",
                f"Espeon joined authorized guild:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})",
                context=EspeonContext.ESPEON,
            )
        else:
            espeon_log(
                "warn",
                f"Espeon joined unauthorized guild and is leaving:\n"
                f"Name: {guild.name}\n"
                f"ID: {guild.id}\n"
                f"Owner: {owner_name} (ID: {owner_id})",
                context=EspeonContext.ESPEON,
            )

            # ⚠️ DM the guild owner about restrictions
            if guild_owner:
                try:
                    await guild_owner.send(
                        f"Hello {owner_name}!\n\n"
                        "Espeon can only function in certain servers under Khy's supervision.\n"
                        "This server is not authorized, so Espeon will be leaving. Thank you for understanding!"
                    )
                except Exception:
                    espeon_log(
                        "warn",
                        f"Could not DM the owner of {guild.name}.",
                        context=EspeonContext.ESPEON,
                    )

            # Leave unauthorized guild
            await guild.leave()

    except Exception as e:
        espeon_log(
            "error",
            f"Error in on_guild_join for guild {guild.name}: {e}",
            include_trace=True,
            exc=e,
            context=EspeonContext.ESPEON,
        )


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
    espeon_log(
        tag="",
        label="🌤️  STATUS ROTATOR",
        message=f"Switching status → {activity_type.name}: {message}",
    )
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )


# ────────────────────────────────────────────
#       💜 Hourly Cache Refresh Loop 💜
# ─────────────────────────────────────────────
@tasks.loop(hours=1, reconnect=True)
async def refresh_all_caches():
    if not hasattr(refresh_all_caches, "already_ran"):
        refresh_all_caches.already_ran = True
        return  # 🚫 Skip the first run
    await load_all_caches(bot)
    processed_rare_catches.clear()  # Clear processed catches every hour
    processed_market_feed_message_ids.clear()  # Clear processed market feed messages every hour
    processed_snipe_ids.clear()  # Clear processed snipe IDs every hour


# ====================
# ▶️ Startup-only Tasks
# ====================
@tasks.loop(count=1)
async def startup_tasks():
    await bot.wait_until_ready()  # ensures bot is fully logged in
    print()
    print("✿ ─── · ─── · ─── · ─── · [🦋 CACHES ] · ─── · ─── · ─── · ─── ✿")
    print()
    # 🔹 Load all caches first and wait for completion
    await load_all_caches(bot)

    print()
    print("✿ ─── · ─── · ─── · ─── · [🌻 CHANGE LOG ] · ─── · ─── · ─── · ─── ✿")
    print()
    await auto_log_new_commands(bot, dry_run=False, enabled=False)
    print()
    print("✿ ─── · ─── · ─── · ─── · [🪐 CHECKLIST ] · ─── · ─── · ─── · ─── ✿")

    # Run the checklist at the very end
    await startup_checklist(bot)

    # ✅ Start the hourly loop AFTER startup (skips first immediate run)
    if not refresh_all_caches.is_running():
        refresh_all_caches.start()
    print()
    print("✿ ─── · ─── · ─── · ─── · [☀️  ESPEON BOT ] · ─── · ─── · ─── · ─── ✿")
    print()


from discord.errors import NotFound


def _get_original_error(error: Exception) -> Exception:
    """Unwrap original error from AppCommandInvokeError chain."""
    e = error
    while hasattr(e, "__cause__") and e.__cause__ is not None:
        e = e.__cause__
    return e


# ── 💜 Unified Command Error Handler 💜 ──
from discord.errors import NotFound


# ── Helper to unwrap original error ──
def _get_original_error(error: Exception) -> Exception:
    """Unwrap original error from AppCommandInvokeError chain."""
    e = error
    while hasattr(e, "__cause__") and e.__cause__ is not None:
        e = e.__cause__
    return e


# ── 💜 Unified Command Error Handler 💜 ──
async def handle_command_error(
    error: Exception, ctx_or_interaction, is_slash: bool = False
):
    """
    Unified handler for prefix and slash command errors.
    Silently ignores CommandNotFound and expired autocomplete.
    """

    # ✅ Ignore "command not found"
    if (is_slash and isinstance(error, app_commands.CommandNotFound)) or (
        not is_slash and isinstance(error, commands.CommandNotFound)
    ):
        return

    # ✅ Ignore autocomplete "Unknown interaction" (user typed too fast)
    original = _get_original_error(error)
    if isinstance(original, NotFound) and is_slash:
        espeon_log("info", "Autocomplete interaction expired — safe to ignore")
        return

    # --- Handle custom role-check failures ---
    role_failures = (
        ClanStaffCheckFailure,
        VIPCheckFailure,
        ClanMemberCheckFailure,
        OwnerCheckFailure,
        OwnerCoownerCheckFailure,
    )
    if isinstance(error, role_failures):
        if is_slash:
            await ctx_or_interaction.response.send_message(
                error.args[0], ephemeral=True
            )
        else:
            await ctx_or_interaction.send(error.args[0], ephemeral=True)
        return

    # --- Fallback for other errors ---
    if is_slash:
        if ctx_or_interaction.response.is_done():
            await ctx_or_interaction.followup.send(
                "❌ Something went wrong.", ephemeral=True
            )
        else:
            await ctx_or_interaction.response.send_message(
                "❌ Something went wrong.", ephemeral=True
            )
        espeon_log(
            "error", f"Slash command error: {error}", context=None, include_trace=True
        )
    else:
        await ctx_or_interaction.send("❌ Something went wrong.", ephemeral=True)
        espeon_log(
            "error", f"Prefix command error: {error}", context=None, include_trace=True
        )


# ── Register Slash Command Error Handler
async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    await handle_command_error(error, interaction, is_slash=True)


bot.tree.error(on_app_command_error)


# ── Register Prefix Command Error Handler
@bot.event
async def on_command_error(ctx: commands.Context, error):
    await handle_command_error(error, ctx, is_slash=False)


# 💜 Startup Checklist
async def startup_checklist(bot: commands.Bot):
    """Print a checklist for loaded components, caches, tasks, and slash commands with clean dividers and checks."""

    checklist = []
    from utils.cache.cache_list import (
        AFK_CACHE,
        WB_PING_CACHE,
        ev_tracker_cache,
        market_alert_cache,
        mr_weakness_user_cache,
    )

    # Divider
    divider = "★━━━━━━━━━━━━━━━━━━━━★"
    checklist.append(divider)

    # 🎀 Cogs loaded
    loaded_cogs_count = len(bot.cogs)
    checklist.append(f"✅ {loaded_cogs_count} 🌼 Cogs Loaded")

    # 🟣 Market alerts

    checklist.append(f"✅ {len(market_alert_cache)} 🦄 Market Alerts Loaded")

    # 🌸 Mr. Weakness cache

    checklist.append(f"✅ {len(mr_weakness_user_cache)} 🌸 MR Weakness Users")

    # 🐼 Mr. Weakness cache
    checklist.append(f"✅ {len(ev_tracker_cache)} 🐼 EV Tracker Users")

    # 🫧 AFK cache
    checklist.append(f"✅ {len(AFK_CACHE)} 🫧 AFK Users")

    # 🦩 World Boss ping cache
    checklist.append(f"✅ {len(WB_PING_CACHE)} 🦩 World Boss Ping Users")

    # 💛 Status rotator
    #checklist.append(f"✅ {status_rotator.is_running()} ✨ Status Rotator Running")

    # 🔴 Startup tasks
    checklist.append(f"✅ {startup_tasks.is_running()} 🖌️ Startup Tasks Running")

    # 🟡 PostgreSQL pool
    pg_status = "Ready" if hasattr(bot, "pg_pool") else "Not Ready"
    checklist.append(f"✅ {pg_status} 🪻  PostgreSQL Pool")

    # ⚡ Slash commands synced
    total_slash_commands = sum(1 for _ in bot.tree.walk_commands())
    checklist.append(f"✅ {total_slash_commands} ⚡ Slash Commands Synced")

    # Ending divider
    checklist.append(divider)

    # Print checklist
    print()  # blank line before
    for item in checklist:
        print(item)
    print()  # blank line after


# 💜 on_ready Event
@bot.event
async def on_ready():
    print()
    print("✿ ─── · ─── · ─── · ─── · [🌤️ ESPEON AWAKE ] · ─── · ─── · ─── · ─── ✿")
    print()
    espeon_log(tag="", message=f"EspeonBot awake as {bot.user}", label="☀️ ESPEON")

    # Sync slash commands
    await bot.tree.sync()
    # espeon_log("ready", "Slash commands synced with Discord successfully!")

    # Just one time status set on startup
    """if not status_rotator.is_running():
        status_rotator.start()w
    activity_type, message = pick_status_tuple()
    await bot.change_presence(
        activity=discord.Activity(type=activity_type, name=message)
    )"""
    await bot.change_presence(activity=discord.Game(name="☀️ /commands"))

    if not startup_tasks.is_running():
        startup_tasks.start()


# 💜 Loading Cogs & Database
@bot.event
async def setup_hook():
    print()
    print(
        "✿ ─── · ─── · ─── · ─── · [🪻  COGS AND DATABASE ] · ─── · ─── · ─── · ─── ✿"
    )
    print()
    espeon_log("ready", "Setting up database and loading cogs...")

    # -------------------- Setup DB --------------------
    try:
        bot.pg_pool = await get_pg_pool()  # returns SafePool
        # Use SafePool fetchval for the version check
        version = await bot.pg_pool.fetchval("SELECT version();")
        espeon_log("db", f"Connected to Postgres (v{version}) via SafePool")
    except Exception as e:
        espeon_log("critical", f"Postgres connection failed: {e}", include_trace=True)

    # -------------------- Load Cogs --------------------
    print()
    print("✿ ─── · ─── · ─── · ─── · [🌟 GROUP COMMANDS ] · ─── · ─── · ─── · ─── ✿")
    print()
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

    # espeon_log("ready", f"All cogs loaded successfully: {loaded_count}")

    # -------------------- Sync Slash Commands --------------------
    try:
        await bot.tree.sync(guild=discord.Object(id=ACTIVE_GUILD_ID))
        # espeon_log("ready", "Slash commands synced to Active Guild!")
    except Exception as e:
        espeon_log("error", f"Guild sync failed: {e}", include_trace=True)

    print()


# 💜 Starting Bot
if __name__ == "__main__":
    load_dotenv()
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        espeon_log("critical", "DISCORD_TOKEN not found in environment. Exiting...")
        exit(1)
    print(
        "✿ ─── · ─── · ─── · ─── · [🌥️  Espeon is starting ] · ─── · ─── · ─── · ─── ✿"
    )
    print()
    espeon_log(tag="", label="☀️  ESPEON", message="EspeonBot is starting...")

    try:
        bot.run(token)
    except Exception as e:
        espeon_log("error", f"Bot crashed during run: {e}", include_trace=True)
        espeon_log("ready", "EspeonBot did not start successfully. Exiting...")
        exit(1)
