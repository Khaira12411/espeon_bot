from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.petal_lace_settings import (
    COLOR,
    DIVIDER,
    SERVER_CURRENCY_EMOJI,
    SERVER_CURRENCY_NAME,
)
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS, KHY_USER_ID
from utils.cache.cache_list import server_shop_cache
from utils.database.server_currency import (
    bought_box,
    get_user_balance,
    update_user_balance,
)
from utils.database.server_shop import format_item_name, remove_item, update_stock
from utils.essentials.loader import pretty_defer
from utils.function.event_func import is_event_active_now_manila
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import EspeonContext, espeon_log


async def buy_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
    amount: int,
):
    """
    Buy an item from the server shop.
    """

    # Check if event is active or khy is viewing for testing
    success, error_msg, context = is_event_active_now_manila()
    if interaction.user.id != KHY_USER_ID:
        # If event is not active and shop is closed or not open, show error message
        if context == "shop_closed" or context == "shop_not_open":
            await interaction.response.send_message(content=error_msg, ephemeral=True)
            espeon_log(
                "info",
                f"User {interaction.user} attempted to view balance but the shop is not open. Reason: {error_msg}",
                source="View Balance Command",
            )
            return

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

    if amount <= 0:
        await loader.error(content="You must purchase at least 1 item.")
        return

    # Get item details
    item = server_shop_cache.get(item_id)
    item_name = item.get("item_name", "Unknown Item")
    price = item.get("price", 0)
    stock = item.get("stock", 0)
    dex = item.get("dex", "N/A")

    # Check stock
    if stock == 0:
        await loader.error(content=f"Sorry, the item '{item_name}' is out of stock.")
        return

    # Fetch user balance
    user = interaction.user
    user_id = interaction.user.id
    user_name = interaction.user.name
    user_balance = await get_user_balance(bot, user_id)
    guild = interaction.guild

    # Check if there are enough items in stock for the requested amount
    if stock > 0 and amount > stock:
        await loader.error(
            content=(
                f"Sorry, there are only {stock} '{item_name}' left in stock. "
                f"You requested {amount}."
            )
        )
        return

    # Calculate total price
    total = price * amount
    # Check if user has enough balance
    if user_balance < total:
        await loader.error(
            content=(
                f"You do not have enough {SERVER_CURRENCY_NAME} to buy '{item_name}'.\n"
                f"You currently have {user_balance} {SERVER_CURRENCY_EMOJI}."
            )
        )
        return
    # Check if user has donated role and doesn't have non weekly role and not donated role
    role_errors = {
        STRAYMONS__ROLES.donated: "You need to have the Donated role to make purchases from the petal lace shop.\n",
        STRAYMONS__ROLES.non_weekly: "Users with the Non-Weekly role cannot make purchases from the petal lace shop.\n",
        STRAYMONS__ROLES.not_donated: "Users with the Not Donated role cannot make purchases from the petal lace shop.\n",
    }
    user_roles = [role.id for role in interaction.user.roles]

    if STRAYMONS__ROLES.donated not in user_roles:
        await loader.error(content=role_errors[STRAYMONS__ROLES.donated])
        return
    for role_id in [STRAYMONS__ROLES.non_weekly, STRAYMONS__ROLES.not_donated]:
        if role_id in user_roles:
            await loader.error(content=role_errors[role_id])
            return

    # Deduct price from user balance
    new_balance = user_balance - total
    await update_user_balance(bot, user_id, user_name, new_balance)
    item_name = format_item_name(item_name, dex=dex)

    # Decrease stock if not unlimited
    if stock > 0:
        new_stock = stock - amount
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
            log_embed_title = f"{item_name} is Out of Stock"
            log_embed_description = (
                f"{user.mention} has purchased the last stock of **{item_name}** for {total} {SERVER_CURRENCY_EMOJI}.\n"
                f"The item has been removed from the Petal Lace Shop.\n"
                f"**New Balance:** {new_balance} {SERVER_CURRENCY_EMOJI}"
            )
        else:
            log_embed_title = f"Item Purchased: {item_name}"
            log_embed_description = (
                f"{user.mention} has purchased {amount} **{item_name}** from the Petal Lace Shop for {total} {SERVER_CURRENCY_EMOJI}.\n"
                f"**Remaining stock:** {new_stock}"
                f"\n**New Balance:** {new_balance} {SERVER_CURRENCY_EMOJI}"
            )
    elif stock == -1:
        log_embed_title = f"Item Purchased: {item_name}"
        log_embed_description = (
            f"{user.mention} has purchased {amount} **{item_name}** from the Petal Lace Shop for {total} {SERVER_CURRENCY_EMOJI}.\n"
            f"**New Balance:** {new_balance} {SERVER_CURRENCY_EMOJI}"
        )
    forward_line_str = f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to hand your prize."
    # Handle special case for boxes
    if "box" in item_name.lower():
        await bought_box(bot, user_id, item_name)
        log_embed_title = f"**Box Purchased:** {item_name}"
        forward_line_str = f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to give you her wish."

    # Success embed
    embed = discord.Embed(
        title="Purchase Successful",
        description=(
            f"You have successfully purchased {amount} **{item_name}** for {total} {SERVER_CURRENCY_EMOJI}!\n"
            f"Your new balance is {new_balance} {SERVER_CURRENCY_EMOJI}.\n\n"
            f"{forward_line_str}"
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
    # Log purchase in server logs channel
    cafe_log_channel_id = STRAYMONS__TEXT_CHANNELS.cafe_logs
    clan_event_log_id = 1076441765059502233
    log_embed = discord.Embed(
        title=log_embed_title,
        description=log_embed_description,
        color=COLOR,
        timestamp=datetime.now(),
    )
    log_embed.set_author(
        name=interaction.user.display_name,
        icon_url=interaction.user.display_avatar.url,
    )
    if item.get("image_link"):
        log_embed.set_thumbnail(url=item["image_link"])

    cafe_log_channel = guild.get_channel(cafe_log_channel_id)
    clan_event_log_channel = guild.get_channel(clan_event_log_id)
    if cafe_log_channel:
        try:
            await send_webhook(
                bot,
                cafe_log_channel,
                embed=log_embed,
            )
        except Exception as e:
            espeon_log(
                tag="error",
                message=(
                    f"Failed to send shop purchase log webhook in channel "
                    f"'{cafe_log_channel.name}' (ID: {cafe_log_channel.id}): {e}"
                ),
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
    if clan_event_log_channel:
        # await clan_event_log_channel.send(embed=log_embed)
        try:
            await send_webhook(
                bot,
                clan_event_log_channel,
                embed=log_embed,
            )
        except Exception as e:
            espeon_log(
                tag="error",
                message=(
                    f"Failed to send shop purchase log webhook in channel "
                    f"'{clan_event_log_channel.name}' (ID: {clan_event_log_channel.id}): {e}"
                ),
                label="🛒 SERVER SHOP",
                context=EspeonContext.ESPEON,
            )
