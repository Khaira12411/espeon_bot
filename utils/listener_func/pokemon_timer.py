import asyncio
import re
from datetime import datetime

import discord
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.current_setup import POKEMEOW_APPLICATION_ID
from utils.cache.timers_cache import timer_cache  # 💜 import your cache
from utils.loggers.espeon_log import espeon_log

# 🗂 Track scheduled "command ready" tasks to avoid duplicates
ready_tasks = {}


async def detect_pokemeow_reply(message: discord.Message):
    """
    Triggered on any message.
    Handles Pokémon ready notifications depending on user's timer cache settings:
      - off → ignore
      - on → ping them in channel
      - on w/o pings → send message w/o mention
      - react → ✅ react to PokéMeow's message
    """
    try:
        """espeon_log(
            "info", f"Received message: {message.content}", source="PokeMeow Timer"
        )"""

        if message.author.id != POKEMEOW_APPLICATION_ID:
            return

        match = re.search(r"\*\*(.+?)\*\* found a wild", message.content)
        if not match:
            return

        username = match.group(1).strip()
        guild = message.guild

        # Match member case-insensitive
        member = discord.utils.find(
            lambda m: m.name.lower() == username.lower()
            or m.display_name.lower() == username.lower(),
            guild.members,
        )
        if not member:
            return

        # -------------------------------
        # 💜 Check timer_cache settings
        # -------------------------------
        user_settings = timer_cache.get(member.id)
        if not user_settings:
            return

        setting = (user_settings.get("pokemon_setting") or "off").lower()

        if setting == "off":
            return

        # Cancel previous ready task if any
        if member.id in ready_tasks and not ready_tasks[member.id].done():
            ready_tasks[member.id].cancel()

        # Schedule behavior depending on setting
        async def notify_ready():
            try:
                await asyncio.sleep(13)

                if setting == "on":
                    await message.channel.send(
                        f"{Espeon_Emoji.pokeball} {member.mention}, your Pokémon command is ready! {Espeon_Emoji.purple_pawprints}"
                    )
                elif setting == "on w/o pings":
                    await message.channel.send(
                        f"{Espeon_Emoji.pokeball} {member.display_name}, your Pokémon command is ready {Espeon_Emoji.purple_pawprints}!"
                    )
                elif setting == "react":
                    await message.add_reaction(Espeon_Emoji.purple_check2)

                """espeon_log(
                    "info",
                    f"Executed Pokémon timer action '{setting}' for {member}",
                    source="PokeMeow Timer",
                )"""
            except asyncio.CancelledError:
                """espeon_log(
                    "info",
                    f"Cancelled scheduled ready notification for {member}",
                    source="PokeMeow Timer",
                )"""
            except Exception as e:
                espeon_log(
                    "error",
                    f"Error in Pokémon timer action for {member}: {e}",
                    include_trace=True,
                    source="PokeMeow Timer",
                )

        ready_tasks[member.id] = asyncio.create_task(notify_ready())

    except Exception as e:
        espeon_log(
            "critical",
            f"Unhandled exception in detect_pokemeow_reply: {e}",
            include_trace=True,
            source="PokeMeow Timer",
        )
