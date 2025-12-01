from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import server_shop_cache
from utils.database.server_currency import get_user_balance, update_user_balance, bought_box
from utils.database.server_shop import format_item_name, remove_item, update_stock
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.listener_func.event_checklist_caught import is_nov_30_101pm_or_later_manila
from utils.function.webhook import send_webhook

async def buy_item_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    item_name: str,
):
    """
    Buy an item from the server shop.
    """

    # Check if it is nov 30 1:01pm manila time or later
    if not is_nov_30_101pm_or_later_manila():
        await interaction.response.send_message(
            content="The Petal Lace Shop is not yet open. Please try again later.",
            ephemeral=True,
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
    user = interaction.user
    user_id = interaction.user.id
    user_name = interaction.user.name
    user_balance = await get_user_balance(bot, user_id)
    guild = interaction.guild

    # Check if user has enough balance
    if user_balance < price:
        await loader.error(
            content=(
                f"You do not have enough Cherry Pins to buy '{item_name}'.\n"
                f"You currently have {user_balance} {CHERRY_PIN}."
            )
        )
        return
    # Check if user has donated role and doesn't have non weekly role and not donated role
    donated_role_id = STRAYMONS__ROLES.donated
    not_donated_role_id = STRAYMONS__ROLES.not_donated
    non_weekly_role_id = STRAYMONS__ROLES.non_weekly
    user_roles = [role.id for role in interaction.user.roles]
    if donated_role_id not in user_roles:
        await loader.error(
            content=(
                "You need to have the Donated role to make purchases from the petal lace shop.\n"
            )
        )
        return
    if non_weekly_role_id in user_roles:
        await loader.error(
            content=(
                "Users with the Non-Weekly role cannot make purchases from the petal lace shop.\n"
            )
        )
        return
    if not_donated_role_id in user_roles:
        await loader.error(
            content=(
                "Users with the Not Donated role cannot make purchases from the petal lace shop.\n"
            )
        )
        return

    # Deduct price from user balance
    new_balance = user_balance - price
    await update_user_balance(bot, user_id, user_name, new_balance)
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
            log_embed_title = f"{item_name} is Out of Stock"
            log_embed_description = (
                f"{user.mention} has purchased the last stock of **{item_name}**.\n"
                f"The item has been removed from the Petal Lace Shop."
            )
        else:
            log_embed_title = f"Item Purchased: {item_name}"
            log_embed_description = (
                f"{user.mention} has purchased **{item_name}** from the Petal Lace Shop.\n"
                f"Remaining stock: {new_stock}."
            )

    # Handle special case for boxes
    if "box" in item_name.lower():
        await bought_box(bot, user_id, item_name)

    # Success embed
    embed = discord.Embed(
        title="Purchase Successful",
        description=(
            f"You have successfully purchased **{item_name}** for {price} {CHERRY_PIN}!\n"
            f"Your new balance is {new_balance} {CHERRY_PIN}.\n\n"
            f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to hand your prize."
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
        #await cafe_log_channel.send(embed=log_embed)
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
        #await clan_event_log_channel.send(embed=log_embed)
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
            