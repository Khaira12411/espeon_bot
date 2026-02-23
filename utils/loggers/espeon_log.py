# 💜 utils/loggers/espeon_log.py
import traceback
from datetime import datetime
from enum import Enum
from typing import Optional, Union

import discord
from discord.ext import commands

from config.straymons_constants import STRAYMONS__TEXT_CHANNELS

# 💌 Bot log + error channels
ESPEON_BOTLOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.bot_logs
ESPEON_ERROR_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.error_logs  # 👈 error channel

# 🔗 Global bot instance (set this on bot startup)
ESPEON_BOT: Optional[commands.Bot] = None


# 🩰 Espeon server context
class EspeonContext(Enum):
    ESPEON = "espeon"
    STRAYMONS = "straymons"


# 💜 Tags
ESPEON_TAGS = {
    "db": "🪻  DB INFO",
    "cmd": "🫐  COMMAND",
    "ready": "💜 READY",
    "error": "💣 ERROR",
    "skip": "🌷 SKIP",
    "sent": "🍇 SENT",
    "warn": "🌹 WARN",
    "critical": "🚨 CRITICAL",
    "schedule_success": "🌸 SCHEDULE",
    "snipe": "✨ SNIPE",
    "market_alert": "💌 MARKET ALERT",
    "market_value": "🏷️ MARKET VALUE",
    "ev": "🪄 EV TRACKER",
}


def set_espeon_bot(bot: commands.Bot):
    """Set the global Espeon bot instance for logging."""
    global ESPEON_BOT
    ESPEON_BOT = bot


def espeon_log(
    tag: Optional[str],
    message: str,
    *,
    label: Optional[str] = None,
    source: Optional[str] = None,
    include_trace: bool = False,
    exc: Optional[BaseException] = None,
    context: Optional[Union[EspeonContext, commands.Cog]] = None,
):
    """Prints a styled log with timestamp and sends error/critical logs to Discord."""

    now = datetime.now().strftime("%H:%M:%S")

    # 🏷️ Context string
    if isinstance(context, commands.Cog):
        context_str = f"[{context.__class__.__name__.upper()}]"
    elif isinstance(context, EspeonContext):
        context_str = f"[{context.name.upper()}]"
    else:
        context_str = ""

    label_str = f"[{label}]" if label else ""

    # 🪻 Prefix tag
    prefix = ESPEON_TAGS.get(tag, "") if tag else ""

    # 📝 Header
    header = (
        f"[{prefix} : {source}]"
        if prefix and source
        else f"[{prefix}]" if prefix else f"[{source}]" if source else ""
    )

    # 📜 Build log message for console
    parts = [f"[{now}]"]
    if header:
        parts.append(header)
    if label_str:
        parts.append(label_str)
    parts.append(message)

    log_message = " ".join(parts)

    # 🔎 Include traceback only for error/critical or if explicitly requested
    trace_text = ""
    if exc and tag in ("error", "critical"):
        trace_text = "".join(
            traceback.format_exception(type(exc), exc, exc.__traceback__)
        )
        log_message += f"\n```py\n{trace_text}```"

    # 🖨️ Print to console
    print(log_message)

    # 🚨 Send only error/critical logs to error channel
    if tag in ("error", "critical") and ESPEON_BOT and ESPEON_ERROR_CHANNEL_ID:
        try:
            channel = ESPEON_BOT.get_channel(ESPEON_ERROR_CHANNEL_ID)
            if channel:
                full_message = f"`{prefix}` {context_str}{label_str} {message}"
                if trace_text:
                    full_message += f"\n```py\n{trace_text}```"

                # ensure within Discord’s 2000 char limit
                if len(full_message) > 2000:
                    full_message = full_message[:1997] + "..."

                ESPEON_BOT.loop.create_task(channel.send(full_message))
        except Exception:
            print(f"[{now}] [🚨 ERROR] Failed to send error log to Discord:")
            traceback.print_exc()
