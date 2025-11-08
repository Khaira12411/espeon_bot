import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.cache.cache_list import server_shop_cache
from utils.database.server_currency import (
    get_user_balance,
    reset_all_balances,
    update_user_balance,
)
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from config.straymons_constants import STRAYMONS__ROLES
# 🟣────────────────────────────────────────────
#           💜 Add Balance
# ─────────────────────────────────────────────
async def add_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int,
):
    """Function to add balance to a user's server currency account."""

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Adding balance to {member.display_name}...",
        ephemeral=False,
    )

    # Fetch current balance
    current_balance = await get_user_balance(
        bot=bot,
        user_id=member.id,
    )

    # Update balance
    new_balance = current_balance + amount
    await update_user_balance(
        bot=bot,
        user_id=member.id,
        new_balance=new_balance,
    )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Updated",
        description=(
            f"Successfully added {CHERRY_PIN}{amount} to {member.mention}'s account.\n"
            f"New Balance: {CHERRY_PIN}{new_balance}"
        ),
        color=COLOR,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=DIVIDER)
    await loader.success(embed=embed, content="")
    espeon_log(
        tag="info",
        message=(
            f"✅ {interaction.user.name} added {amount} to {member.name} "
            f"in server currency. New balance: {new_balance}."
        ),
        context=EspeonContext.SERVER_CURRENCY,
    )

    # TODO Log the balance update action


# 🟣────────────────────────────────────────────
#           💜 Remove Balance
# ─────────────────────────────────────────────
async def remove_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member,
    amount: int,
):
    """Function to remove balance from a user's server currency account."""

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content=f"Removing balance from {member.display_name}...",
        ephemeral=False,
    )

    # Fetch current balance
    current_balance = await get_user_balance(
        bot=bot,
        user_id=member.id,
    )

    # Update balance
    new_balance = max(0, current_balance - amount)  # Prevent negative balance
    await update_user_balance(
        bot=bot,
        user_id=member.id,
        new_balance=new_balance,
    )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Updated",
        description=(
            f"Successfully removed {CHERRY_PIN}{amount} from {member.mention}'s account.\n"
            f"New Balance: {CHERRY_PIN}{new_balance}"
        ),
        color=COLOR,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=DIVIDER)
    await loader.success(embed=embed, content="")
    espeon_log(
        tag="info",
        message=(
            f"✅ {interaction.user.name} removed {amount} from {member.name} "
            f"in server currency. New balance: {new_balance}."
        ),
        context=EspeonContext.SERVER_CURRENCY,
    )

    # TODO Log the balance update action

# 🟣────────────────────────────────────────────
#           💜 Reset Balance
# ─────────────────────────────────────────────
async def reset_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member = None,
    all_users: bool = False,
):
    """Function to reset balance for a user or all users in server currency."""

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Resetting balance...",
        ephemeral=False,
    )


    if all_users:
        # Reset balance for all users
        await reset_all_balances(bot=bot)
        description = "Successfully reset balance for all users to 0."
        espeon_log(
            tag="info",
            message=f"✅ {interaction.user.name} reset balance for all users.",
            context=EspeonContext.SERVER_CURRENCY,
        )
    else:
        # Reset balance for a specific user
        if member is None:
            await loader.error(
                content="Error: No member specified for balance reset."
            )
            return

        await update_user_balance(
            bot=bot,
            user_id=member.id,
            new_balance=0,
        )
        description = f"Successfully reset {member.mention}'s balance to 0."
        espeon_log(
            tag="info",
            message=f"✅ {interaction.user.name} reset balance for {member.name}.",
            context=EspeonContext.SERVER_CURRENCY,
        )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Reset",
        description=description,
        color=COLOR,
        timestamp=datetime.datetime.utcnow(),
    )
    embed.set_footer(text=DIVIDER)
    await loader.success(embed=embed, content="")

    # TODO Log the balance reset action

# 🟣────────────────────────────────────────────
#           💜 View Balance
# ─────────────────────────────────────────────
async def view_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member = None,
):
    """
    Check your Cherry Pin balance.
    """
    # TODO Only allow staff to see other users' balances

    user_str = "your" if member is None else f"{member.display_name}'s"
    target_user = interaction.user if member is None else member
    # Defer
    loader = await pretty_defer(
        interaction=interaction, content=f"Fetching {user_str} balance...", ephemeral=True
    )

    # Fetch user balance
    user_id = target_user.id
    user_balance = await get_user_balance(bot, user_id)

    # Build embed
    title_str = "Your" if member is None else f"{member.display_name}'s"
    desc_str = "You currently have" if member is None else f"{member.display_name} currently has"
    embed = discord.Embed(
        title=f"🍒 {title_str} Cherry Pin Balance 🍒",
        description=f"{desc_str} **{CHERRY_PIN} {user_balance}**.",
        color=COLOR,
        timestamp=datetime.datetime.now(),
    )
    embed.set_image(url=DIVIDER)

    await loader.success(embed=embed, content="")
    if not member:
        log_str = f"✅ {interaction.user.name} viewed their balance: {user_balance}."
    else:
        log_str = f"✅ {interaction.user.name} viewed {user_str} balance: {user_balance}."

    espeon_log(
        tag="info",
        message=log_str,
        context=EspeonContext.SERVER_CURRENCY,
    )