import re

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import CHERRY_PIN, COLOR
from utils.database.server_shop import format_item_name, upsert_item
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import design_embed, get_pokemon_gif


async def add_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    price: int,
    stock: int,
):
    """
    Add or update an item in the server shop.
    """
    image_link = None
    if "coins" in item_name.lower():
        image_link = None

    else:
        # Clean item name and remove # and dex number if present
        item_name = re.sub(r"\s*#\d+$", "", item_name)
        espeon_log(
            tag="debug",
            message=(f"Cleaned item name: {item_name}"),
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        gif_url = get_pokemon_gif(item_name)
        espeon_log(
            tag="debug",
            message=(f"Fetched GIF URL for item '{item_name}': {gif_url}"),
            label="🛒 SERVER SHOP",
            context=EspeonContext.ESPEON,
        )
        image_link = gif_url if gif_url else None

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Adding item to shop...", ephemeral=True
    )
    # Upsert item in the database
    item_id = await upsert_item(
        bot=bot, item_name=item_name, price=price, stock=stock, image_link=image_link
    )
    if not item_id:
        await loader.error("Failed to add item to the shop. Please try again later.")
        return

    # Success embed
    display_name = format_item_name(item_name)
    embed = discord.Embed(
        title="Item Added to Shop",
        description=(
            f"**Item Name:** {display_name}\n"
            f"**Item ID:** `{item_id}`\n"
            f"**Price:** {price} {CHERRY_PIN}\n"
            f"**Stock:** {stock}\n"
        ),
        color=COLOR,
    )
    if image_link:
        embed.set_thumbnail(url=image_link)
    await loader.success(embed=embed, content="")
    espeon_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) added item "
            f"'{item_name}' (item_id: {item_id}, price: {price}, stock: {stock}) in the server shop."
        ),
        label="🛒 SERVER SHOP",
        context=EspeonContext.ESPEON,
    )
