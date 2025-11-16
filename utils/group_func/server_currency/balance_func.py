from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.aesthetic import Espeon_Emoji
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES
from utils.cache.cache_list import server_shop_cache
from utils.database.server_currency import (
    get_user_balance,
    reset_all_balances,
    update_user_balance,
    upsert_user_balance,
)
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log


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
    if current_balance is None:
        # Upsert user with initial balance if not found
        await upsert_user_balance(bot, member.id, member.name, amount)
        new_balance = amount
    else:
        # Update balance
        new_balance = current_balance + amount
        await update_user_balance(
            bot=bot,
            user_id=member.id,
            user_name=member.name,
            new_balance=new_balance,
        )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Updated",
        description=(
            f"Successfully added {amount} {CHERRY_PIN} to {member.mention}'s account.\n"
            f"New Balance: {new_balance} {CHERRY_PIN}"
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=DIVIDER)
    await loader.success(embed=embed, content="")
    espeon_log(
        tag="info",
        message=(
            f"✅ {interaction.user.name} added {amount} to {member.name} "
            f"in server currency. New balance: {new_balance}."
        ),
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
    if current_balance is None:
        current_balance = 0
        # Upsert user with 0 balance if not found
        await upsert_user_balance(bot, member.id, member.name)
        # Exit early since balance is already 0
        await loader.error(
            content=f"{member.mention} has a balance of 0 {CHERRY_PIN}. Cannot remove balance."
        )
        return

    # Update balance
    new_balance = max(0, current_balance - amount)  # Prevent negative balance
    await update_user_balance(
        bot=bot,
        user_id=member.id,
        user_name=member.name,
        new_balance=new_balance,
    )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Updated",
        description=(
            f"Successfully removed {amount} {CHERRY_PIN} from {member.mention}'s account.\n"
            f"New Balance: {new_balance} {CHERRY_PIN}"
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_author(
        name=interaction.user.display_name, icon_url=interaction.user.display_avatar.url
    )
    embed.set_thumbnail(url=member.display_avatar.url)
    embed.set_image(url=DIVIDER)
    await loader.success(embed=embed, content="")
    espeon_log(
        tag="info",
        message=(
            f"✅ {interaction.user.name} removed {amount} from {member.name} "
            f"in server currency. New balance: {new_balance}."
        ),
    )

    # TODO Log the balance update action


# 🟣────────────────────────────────────────────
#           💜 Reset Balance
# ─────────────────────────────────────────────
async def reset_balance_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
    member: discord.Member = None,
    all_users: str = None,
):
    """Function to reset balance for a user or all users in server currency."""

    # Defer the interaction to allow more time for processing
    loader = await pretty_defer(
        interaction=interaction,
        content="Resetting balance...",
        ephemeral=False,
    )

    if all_users.lower() == "yes":
        # Reset balance for all users
        await reset_all_balances(bot=bot)
        description = "Successfully reset balance for all users to 0."
        espeon_log(
            tag="info",
            message=f"✅ {interaction.user.name} reset balance for all users.",
        )
    else:
        # Reset balance for a specific user
        if member is None:
            await loader.error(content="Error: No member specified for balance reset.")
            return

        await update_user_balance(
            bot=bot,
            user_name=member.name,
            user_id=member.id,
            new_balance=0,
        )
        description = f"Successfully reset {member.mention}'s {CHERRY_PIN} to 0."
        espeon_log(
            tag="info",
            message=f"✅ {interaction.user.name} reset balance for {member.name}.",
        )

    # Send confirmation message
    embed = discord.Embed(
        title="Balance Reset",
        description=description,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_image(url=DIVIDER)
    if all_users.lower() != "yes":
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        if member:
            embed.set_thumbnail(url=member.display_avatar.url)
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
        interaction=interaction,
        content=f"Fetching {user_str} balance...",
        ephemeral=False,
    )

    # Fetch user balance
    user_id = target_user.id
    user_balance = await get_user_balance(bot, user_id)
    if user_balance is None:
        user_balance = 0
        # Upsert user with 0 balance if not found
        await upsert_user_balance(bot, user_id, target_user.name)

    # Build embed
    title_str = "Your" if member is None else f"{member.display_name}'s"
    embed = discord.Embed(
        title=f"🍒 {title_str} Cherry Pin Balance 🍒",
        description=f"**{user_balance} {CHERRY_PIN}**.",
        color=COLOR,
        timestamp=datetime.now(),
    )
    author_name = (
        interaction.user.display_name if member is None else member.display_name
    )
    author_icon_url = (
        interaction.user.display_avatar.url
        if member is None
        else member.display_avatar.url
    )
    embed.set_author(name=author_name, icon_url=author_icon_url)
    embed.set_image(url=DIVIDER)
    view = Cherry_Pin_Reward_Info(interaction.user)

    await loader.success(embed=embed, content="", view=view)
    if not member:
        log_str = f"✅ {interaction.user.name} viewed their balance: {user_balance}."
    else:
        log_str = (
            f"✅ {interaction.user.name} viewed {user_str} balance: {user_balance}."
        )

    espeon_log(
        tag="info",
        message=log_str,
    )


class Cherry_Pin_Reward_Info(View):
    def __init__(self, user, timeout=180):
        super().__init__(timeout=timeout)
        self.user = user

    @discord.ui.button(
        label="Info",
        emoji=Espeon_Emoji.pink_flower_two,
        style=discord.ButtonStyle.secondary,
        custom_id="cherry_pin_reward_info_button",
    )
    async def info_button(self, interaction: discord.Interaction, button: Button):
        # Only user who invoked can use the button
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You cannot use this button.", ephemeral=True
            )
            return
        embed = discord.Embed(
            title="🍒 Cherry Pin Rewards Info 🍒",
            description=(
                f"Legendary – 1 {CHERRY_PIN}\n"
                f"Shiny checklist – 2 {CHERRY_PIN}\n"
                f"Fishing exclusive checklist (if any) – 2 {CHERRY_PIN}\n"
                f"Shiny full-odds – 2 {CHERRY_PIN}\n"
                f"Exclusive checklist – 3 {CHERRY_PIN}\n"
                f"Fishing legendary – 3 {CHERRY_PIN}\n"
                f"Fishing shiny – 4 {CHERRY_PIN}\n"
                f"Fishing shiny exclusive checklist (if any) – 5 {CHERRY_PIN}\n"
                f"Shiny legendary full-odds – 5 {CHERRY_PIN}"
            ),
            color=COLOR,
            timestamp=datetime.now(),
        )
        embed.set_image(url=DIVIDER)
        embed.set_author(
            name=interaction.user.display_name,
            icon_url=interaction.user.display_avatar.url,
        )
        # Edit original message
        await interaction.response.edit_message(embed=embed, view=self)
