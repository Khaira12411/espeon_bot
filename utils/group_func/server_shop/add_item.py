import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import COLOR, CHERRY_PIN
from utils.database.server_shop import upsert_item
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

    if "coins" in item_name.lower():
        image_link = None

    else:
        gif_url = get_pokemon_gif(item_name)
        image_link = gif_url if gif_url else None

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Adding item to shop...", ephemeral=True
    )
    # Upsert item in the database
    item_id = await upsert_item(bot, item_name, price, stock, image_link)
    if not item_id:
        await loader.error("Failed to add item to the shop. Please try again later.")
        return

    # Success embed
    embed = discord.Embed(
        title="Item Added to Shop",
        description=(
            f"**Item ID:** `{item_id}`\n"
            f"**Item Name:** {item_name}\n"
            f"**Price:** {price} {CHERRY_PIN}\n"
            f"**Stock:** {stock}\n"
        ),
        color=COLOR,
    )
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
