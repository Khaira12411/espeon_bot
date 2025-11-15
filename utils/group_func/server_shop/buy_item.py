from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.cache.cache_list import server_shop_cache
from utils.database.server_currency import get_user_balance, update_user_balance
from utils.database.server_shop import format_item_name, remove_item, update_stock
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from config.aesthetic import Espeon_Emoji

async def buy_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
):
    """
    Buy an item from the server shop.
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction, content="Processing your purchase...", ephemeral=False
    )

    # Fetch item from cache
    from utils.cache.server_shop_cache import fetch_shop_item_id_by_name

    item_id = fetch_shop_item_id_by_name(item_name)
    if not item_id:
        await loader.error(content=f"Item '{item_name}' does not exist in the shop.")
        return

    # Get item details
    item = server_shop_cache.get(item_id)
    item_name = item.get("item_name", "Unknown Item")
    price = item.get("price", 0)
    stock = item.get("stock", 0)

    # Check stock
    if stock == 0:
        await loader.error(content=f"Sorry, the item '{item_name}' is out of stock.")
        return

    # Fetch user balance
    user_id = interaction.user.id
    user_balance = await get_user_balance(bot, user_id)

    # Check if user has enough balance
    if user_balance < price:
        await loader.error(
            content=(
                f"You do not have enough Cherry Pins to buy '{item_name}'.\n"
                f"You currently have {user_balance} {CHERRY_PIN}."
            )
        )
        return

    # Deduct price from user balance
    new_balance = user_balance - price
    await update_user_balance(bot, user_id, new_balance)
    item_name = format_item_name(item_name)

    # Decrease stock if not unlimited
    if stock > 0:
        new_stock = stock - 1
        await update_stock(bot, item_id, new_stock)
        if new_stock == 0:
            # Remove from database
            await remove_item(bot, item_id)
            espeon_log(
                tag="info",
                message=(
                    f"Item '{item_name}' (item_id: {item_id}) is out of stock and has been removed from the shop."
                ),
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )

    # Success embed
    embed = discord.Embed(
        title="Purchase Successful",
        description=(
            f"You have successfully purchased **{item_name}** for {price} {CHERRY_PIN}!\n"
            f"Your new balance is {new_balance} {CHERRY_PIN}.\n\n"
            f"{Espeon_Emoji.pink_flower} Please present this message to skaia to claim your prize."
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_image(url=DIVIDER)
    if item.get("image_link"):
        embed.set_thumbnail(url=item["image_link"])

    await loader.success(embed=embed, content="")
    espeon_log(
        tag="cmd",
        message=(
            f"User {interaction.user} ({interaction.user.id}) purchased item "
            f"'{item_name}' (item_id: {item_id}, price: {price}) from the server shop."
        ),
        label="🛒 SERVER SHOP",
        context=EspeonContext.ESPEON,
    )

    # TODO Send purchase logs to a specific channel
