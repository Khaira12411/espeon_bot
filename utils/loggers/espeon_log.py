# 💜 utils/loggers/espeon_log.py
import traceback
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__TEXT_CHANNELS

# 💌 Bot log channel
ESPEON_BOTLOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.bot_logs


# 🩰 Espeon server context
class EspeonContext(Enum):
    ESPEON = "espeon"
    STRAYMONS = "straymons"


# 💜 Tags
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
    tag: Optional[str],
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

    now = datetime.now().strftime("%H:%M:%S")

    # Determine context string
    if isinstance(context, commands.Cog):
        context_str = f"[{context.__class__.__name__.upper()}]"
    elif isinstance(context, EspeonContext):
        context_str = f"[{context.name.upper()}]"
    else:
        context_str = ""

    label_str = f"[{label}]" if label else ""

    # Determine prefix (empty if tag is None or "")
    prefix = ESPEON_TAGS.get(tag, "") if tag else ""

    # Compose header
    header = (
        f"[{prefix} : {source}]"
        if prefix and source
        else f"[{prefix}]" if prefix else f"[{source}]" if source else ""
    )

    # Compose final log message cleanly
    parts = [f"[{now}]"]
    if header:
        parts.append(header)
    if label_str:
        parts.append(label_str)
    parts.append(message)

    log_message = " ".join(parts)

    # Add traceback if needed
    if include_trace and exc:
        log_message += f"\n```py\n{''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))}```"

    print(log_message)

    # 🚨 Send error/critical logs to bot log channel
    if tag in ("error", "critical") and bot and ESPEON_BOTLOG_CHANNEL_ID:
        try:
            channel = bot.get_channel(ESPEON_BOTLOG_CHANNEL_ID)
            if channel:
                full_message = f"`{prefix}` {context_str}{label_str} {message}"
                if len(full_message) > 2000:
                    full_message = full_message[:1997] + "..."
                bot.loop.create_task(channel.send(full_message))
        except Exception:
            print(f"[{now}] [🚨 ERROR] Failed to send error/critical log to Discord:")
            traceback.print_exc()
