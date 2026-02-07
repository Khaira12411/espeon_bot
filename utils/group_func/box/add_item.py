import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import COLOR, SERVER_CURRENCY_EMOJI
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
from utils.cache.global_variable import log_event_enabled
from utils.database.box_prize_db import add_box_prize, fetch_box_prize
from utils.database.server_shop import (
    fetch_item_by_name,
    format_item_name,
    update_stock,
    upsert_item,
)
from utils.essentials.get_dex import get_dex
from utils.essentials.loader import pretty_defer
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, get_pokemon_gif


async def log_event(bot, embed: discord.Embed, channel: discord.TextChannel):
    """Log event changes to the designated log channel via webhook if logging is enabled."""
    if not log_event_enabled:
        espeon_log(
            tag="debug",
            message="Event logging is currently disabled. Skipping log.",
            label="🎁 Event Log",
        )
        return

    if channel.id == STRAYMONS__TEXT_CHANNELS.cafe_logs:
        guild = channel.guild
        clan_event_log_channel = guild.get_channel(
            STRAYMONS__TEXT_CHANNELS.clan_event_log
        )
        log_channels = [channel, clan_event_log_channel]
        for log_channel in log_channels:
            await send_webhook(
                channel=log_channel,
                embed=embed,
                bot=bot,
            )
    else:
        await send_webhook(
            channel=channel,
            embed=embed,
            bot=bot,
        )


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    box_name: str,
    item_name: str,
):
    """Add an item to a box in the database."""
    stock = 1  # Default stock for box items is always 1
    # Defer the response
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding {item_name} to {box_name}...",
        ephemeral=False,
    )
    # Get image link for the item
    image_link = None
    gif_url = get_pokemon_gif(item_name)
    espeon_log(
        tag="debug",
        message=(f"Fetched GIF URL for item '{item_name}': {gif_url}"),
        label="🎁 BOX PRIZE",
        context=EspeonContext.ESPEON,
    )
    image_link = gif_url if gif_url else None

    # Get dex number for the item
    dex = get_dex(item_name)

    # Add item to the box in the database
    try:
        await add_box_prize(
            bot=bot,
            prize=item_name,
            box_name=box_name,
            stock=stock,
            dex=dex,
            image_link=image_link,
        )
        # Check if box exists
        existing_box = await fetch_item_by_name(bot, item_name=box_name)
        if not existing_box:
            # Upsert box in the database if it doesn't exist
            box_id = await upsert_item(
                bot=bot,
                item_name=box_name,
                price=10,
                stock=1,
                image_link=None,
                description=None,
                dex=None,
            )
        else:
            # Update stock of the box if it already exists
            box_id = existing_box.get("item_id")
            old_stock = existing_box.get("stock", 0)
            new_stock = old_stock + 1
            await update_stock(bot=bot, item_id=box_id, stock=new_stock)

    except Exception as e:
        espeon_log(
            tag="warn",
            message=f"⚠️ Failed to add item '{item_name}' to box '{box_name}': {e}",
            exc=e,
            label="🎁 BOX PRIZE DB",
            context=EspeonContext.ESPEON,
        )
        await loader.error(content=f"⚠️ Failed to add {item_name} to {box_name}.")
        return

    # Build success embed
    display_name = format_item_name(item_name, dex=dex)
    embed = discord.Embed(
        title=f"New Box Item Added!",
        description=(
            f"- **Item Name:** {display_name}\n"
            f"- **Box Name:** {box_name}\n"
            f"- **Stock:** {stock}\n"
        ),
        timestamp=datetime.now(),
        color=COLOR,
    )
    embed = design_embed(embed=embed, user=interaction.user, thumbnail_url=image_link)
    await loader.success(content="", embed=embed)
    # Send webhook notification
    log_channel = interaction.guild.get_channel(STRAYMONS__TEXT_CHANNELS.bot_logs)
    await log_event(bot=bot, embed=embed, channel=log_channel)
