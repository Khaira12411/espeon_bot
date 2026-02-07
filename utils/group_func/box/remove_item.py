import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import COLOR, SERVER_CURRENCY_EMOJI
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.database.box_prize_db import (
    fetch_box_prize,
    fetch_box_prize_with_box,
    remove_box_prize,
)
from utils.database.server_shop import format_item_name
from utils.essentials.get_dex import get_dex
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, get_pokemon_gif

from .add_item import log_event

async def remove_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    box_name: str,
    item_name: str,
):
    """Remove an item from a box in the database."""
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Removing {item_name} from {box_name}...",
        ephemeral=False,
    )

    #  Check if the item exists in the box
    existing_prize = await fetch_box_prize_with_box(
        bot, box_name=box_name, prize=item_name
    )

    if not existing_prize:
        await loader.error(content=f"{item_name} is not in {box_name}.")
        return

    # Get data for the item to be removed (for logging purposes)
    dex = existing_prize.get("dex")
    image_link = existing_prize.get("image_link")
    stock = existing_prize.get("stock")

    # Remove the item from the box in the database
    try:
        await remove_box_prize(bot=bot, box_name=box_name, prize=item_name)
        espeon_log(
            tag="info",
            message=f"✅ Successfully removed item '{item_name}' from box '{box_name}'.",
            label="🎁 BOX PRIZE",
            context=EspeonContext.ESPEON,
        )
    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to remove item '{item_name}' from box '{box_name}': {e}",
            label="🎁 BOX PRIZE",
            context=EspeonContext.ESPEON,
        )
        await loader.error(content=f"Failed to remove {item_name} from {box_name}.")
        return

    # Build success embed
    display_name = format_item_name(item_name, dex=dex)
    embed = discord.Embed(
        title=f"Removed {display_name} from {box_name}",
        description=(
            f"Successfully removed **{display_name}** from **{box_name}**.\n"
            f"**Dex Number:** {dex}\n"
            f"**Stock:** {stock}\n"
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed = design_embed(embed=embed, user=interaction.user, thumbnail_url=image_link)
    await loader.success(content="", embed=embed)

    # Send webhook notification
    log_channel = interaction.guild.get_channel(STRAYMONS__TEXT_CHANNELS.bot_logs)
    await log_event(bot=bot, embed=embed, channel=log_channel)
