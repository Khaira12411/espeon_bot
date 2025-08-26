# 💜 utils/loggers/espeon_log.py
import traceback
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__TEXT_CHANNELS

# 💌 Set this to your bot log channel ID
ESPEON_BOTLOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.bot_logs


# 🩰 Espeon server context
class EspeonContext(Enum):
    ESPEON = "espeon"
    STRAYMONS = "straymons"


# 💜 Purple/Pink themed tags (🚨 red for critical)
ESPEON_TAGS = {
    "db": "🪻  DB INFO",
    "cmd": "🫐 COMMAND",
    "ready": "💜 READY",
    "error": "💣 ERROR",
    "skip": "🌷 SKIP",
    "sent": "🍇 SENT",
    "warn": "🌹 WARN",
    "critical": "🚨 CRITICAL",
    "schedule_success": "🌸 SCHEDULE",
}


def espeon_log(
    tag: str,
    message: str,
    *,
    label: Optional[str] = None,
    source: Optional[str] = None,
    bot: Optional[commands.Bot] = None,
    include_trace: bool = False,
    exc: Optional[BaseException] = None,
    context: Optional[Union[EspeonContext, commands.Cog]] = None,
):
    """Prints a styled log with timestamp and sends error/critical logs to Discord."""

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Determine context string
    if isinstance(context, commands.Cog):
        context_str = f"[{context.__class__.__name__.upper()}]"
    elif isinstance(context, EspeonContext):
        context_str = f"[{context.name.upper()}]"
    else:
        context_str = ""

    label_str = f"[{label}]" if label else ""
    prefix = ESPEON_TAGS.get(tag, "💜 NOTE")

    # Compose header
    header = f"[{prefix} : {source}]" if source else f"[{prefix}]"

    # Compose traceback if needed
    trace_text = ""
    if include_trace and exc:
        trace_text = f"\n```py\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}```"

    # Print log locally
    log_message = (
        f"[{now}] {header} {context_str}{label_str} {message}{trace_text}".strip()
    )
    print(log_message)

    # 🚨 Send error/critical logs to bot log channel
    if tag in ("error", "critical") and bot and ESPEON_BOTLOG_CHANNEL_ID:
        try:
            channel = bot.get_channel(ESPEON_BOTLOG_CHANNEL_ID)
            if channel:
                full_message = (
                    f"`{prefix}` {context_str}{label_str} {message}{trace_text}"
                )
                if len(full_message) > 2000:
                    full_message = full_message[:1997] + "..."
                bot.loop.create_task(channel.send(full_message))
        except Exception:
            print(f"[{now}] [🚨 ERROR] Failed to send error/critical log to Discord:")
            traceback.print_exc()
