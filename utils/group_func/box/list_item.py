import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import COLOR, SERVER_CURRENCY_EMOJI
from config.straymons_constants import STRAYMONS__EMOJIS, STRAYMONS__TEXT_CHANNELS
from utils.database.box_prize_db import (
    add_box_prize,
    fetch_all_box_prizes,
    fetch_box_prize,
)
from utils.database.server_shop import format_item_name
from utils.essentials.get_dex import get_dex
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, get_pokemon_gif


def strip_emoji(item_name):
    # Remove Discord custom emoji (e.g., <...>) and leading emoji/spaces
    item_name = re.sub(r"^<[^>]+>\s*", "", item_name)
    item_name = re.sub(r"^[^a-zA-Z0-9#]+\s*", "", item_name)
    return item_name


async def list_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """List all items in a box."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Fetching box items...",
        ephemeral=False,
    )

    # Fetch all box prizes from the database
    box_prizes = await fetch_all_box_prizes(bot)
    if not box_prizes:
        await loader.error(content="No items found in any box.")
        return

    # Create dict for each box with list of items categorized by type (golden, shiny, legendary)
    categorized_boxes = {}
    for box_name, prizes in box_prizes.items():
        golden_list = []
        shiny_list = []
        legendary_list = []
        for prize_name, prize_info in prizes.items():
            item_name = format_item_name(prize_name)
            item_name_no_emoji = strip_emoji(item_name)
            if "golden" in item_name.lower():
                golden_list.append(item_name_no_emoji)
            elif "shiny" in item_name.lower():
                shiny_list.append(item_name_no_emoji)
            elif "legendary" in item_name.lower():
                legendary_list.append(item_name_no_emoji)
        categorized_boxes[box_name] = {
            "golden": golden_list,
            "shiny": shiny_list,
            "legendary": legendary_list,
        }
    # Now categorized_boxes is in the format:
    # {
    #   'box_1': {'golden': [...], 'shiny': [...], 'legendary': [...]},
    #   ...
    # }

    # Create embed
    embed = discord.Embed(
        title="Box Items",
        description="Here are the items currently in the boxes:",
        color=COLOR,
    )
    for box_name, categories in categorized_boxes.items():
        field_name = f"**{box_name}**"
        legendary_mons_str = (
            f"{STRAYMONS__EMOJIS.legendary}" + (", ".join(categories["legendary"]))
            if categories["legendary"]
            else ""
        )
        shiny_mons_str = (
            f"{STRAYMONS__EMOJIS.shiny}" + (", ".join(categories["shiny"]))
            if categories["shiny"]
            else ""
        )
        golden_mons_str = (
            f"{STRAYMONS__EMOJIS.golden11}" + (", ".join(categories["golden"]))
            if categories["golden"]
            else ""
        )
        field_value = "\n".join(
            filter(
                None,
                [
                    golden_mons_str,
                    shiny_mons_str,
                    legendary_mons_str,
                ],
            )
        )
        embed.add_field(name=field_name, value=field_value, inline=False)
    await loader.success(content="", embed=embed)
