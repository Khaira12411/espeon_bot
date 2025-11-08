import datetime
import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import CHERRY_PIN, COLOR
from utils.cache.cache_list import server_shop_cache
from utils.database.server_shop import fetch_item_by_id, update_item
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log


async def edit_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    new_item_name: str = None,
    new_price: int = None,
    new_stock: int = None,
    new_image_link: str = None,
):
    """
    Edit an existing item in the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Editing item in shop...", ephemeral=True
    )

    # Fetch existing item in cache to check if it exists
    from utils.cache.server_shop_cache import fetch_shop_item_id_by_name
    item_id = fetch_shop_item_id_by_name(item_name)
    if not item_id:
        await loader.error(content=f"Item '{item_name}' does not exist in the shop.")
        return
    
    existing_item = server_shop_cache.get(item_id)

    # Check if user provided at least one field to update
    if (
        new_item_name is None
        and new_price is None
        and new_stock is None
        and new_image_link is None
    ):
        await loader.error(content="Please provide at least one field to update.")
        return

    # Update item in the database
    await update_item(
        bot,
        item_id,
        new_item_name,
        new_price,
        new_stock,
        new_image_link,
    )

    # Success embed
    embed = discord.Embed(
        title="Item Edited in Shop",
        description=f"**Item ID:** `{item_id}`",
        color=COLOR,
        timestamp=datetime.now(),
    )
    if new_item_name is not None:
        value_str = f"> - **Old:** {existing_item['item_name']}\n> - **New:** {new_item_name}"
        embed.add_field(name="Item Name", value=new_item_name, inline=False)

    if new_price is not None:
        value_str = f"> - **Old:** {existing_item['price']} {CHERRY_PIN}\n> - **New:** {new_price} {CHERRY_PIN}"
        embed.add_field(name="Price", value=value_str, inline=False)

    if new_stock is not None:
        value_str = f"> - **Old:** {existing_item['stock']}\n> - **New:** {new_stock}"
        embed.add_field(name="Stock", value=value_str, inline=False)

    if new_image_link is not None:
        value_str = f"> - **Old:** {existing_item['image_link']}\n> - **New:** {new_image_link}"
        embed.add_field(name="Image Link", value=value_str, inline=False)

    if new_image_link is not None:
        embed.set_thumbnail(url=new_image_link)
    elif old_image_link := existing_item.get("image_link"):
        embed.set_thumbnail(url=old_image_link)

    await loader.success(embed=embed, content="")
    espeon_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) edited item "
            f"'{item_id}' in the server shop."
        ),
        label="🛒 SERVER SHOP",
        context=EspeonContext.ESPEON,
    )

    # TODO  Send logs to a specific channel
