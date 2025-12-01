from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.aesthetic import Espeon_Emoji
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import server_shop_cache, user_balance_cache
from utils.database.server_currency import (
    get_user_balance,
    reset_all_balances,
    update_user_balance,
    upsert_user_balance,
)
from utils.essentials.loader import pretty_defer
from utils.listener_func.event_checklist_caught import is_nov_30_101pm_or_later_manila
from utils.loggers.espeon_log import EspeonContext, espeon_log

LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.server_logs
BOX_MAP = {
    "daisyia": {
        "quest": "Hatch any shiny from an egg.",
    },
    "gardelette": {
        "quest": "Attain all weekly roles for that week",
    },
    "melaryne": {
        "quest": "Claim the checklist reward",
    },
}


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

    # Log the balance update action
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title=f"{CHERRY_PIN} Cherry Pin Balance Updated",
            description=(
                f"**User:** {member.mention}\n"
                f"**Added by:** {interaction.user.mention}\n"
                f"**Amount Added:** {amount} {CHERRY_PIN}\n"
                f"**New Balance:** {new_balance} {CHERRY_PIN}"
            ),
            color=COLOR,
            timestamp=datetime.now(),
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        log_embed.set_author(
            name=member.display_name, icon_url=member.display_avatar.url
        )
        log_embed.set_footer(
            text=f"User ID: {member.id}", icon_url=member.display_avatar.url
        )
        await log_channel.send(embed=log_embed)


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

    # Log the balance update action
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title=f"{CHERRY_PIN} Cherry Pin Balance Updated",
            description=(
                f"**User:** {member.mention}\n"
                f"**Removed by:** {interaction.user.mention}\n"
                f"**Amount Removed:** {amount} {CHERRY_PIN}\n"
                f"**New Balance:** {new_balance} {CHERRY_PIN}"
            ),
            color=COLOR,
            timestamp=datetime.now(),
        )
        log_embed.set_thumbnail(url=member.display_avatar.url)
        log_embed.set_author(
            name=member.display_name, icon_url=member.display_avatar.url
        )
        log_embed.set_footer(
            text=f"User ID: {member.id}", icon_url=member.display_avatar.url
        )
        await log_channel.send(embed=log_embed)


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
    # Check if user is owner
    owner_role_id = STRAYMONS__ROLES.clan_owner
    if owner_role_id not in [role.id for role in interaction.user.roles]:
        await loader.error(
            content="You do not have permission to reset balances. Only the server owner can perform this action."
        )
        return

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

    # Log the balance reset action
    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        log_embed = discord.Embed(
            title=f"{CHERRY_PIN} Cherry Pin Balance Reset",
            description=description,
            color=COLOR,
            timestamp=datetime.now(),
        )
        if all_users.lower() != "yes" and member:
            log_embed.set_thumbnail(url=member.display_avatar.url)
            log_embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            log_embed.set_footer(
                text=f"User ID: {member.id}", icon_url=member.display_avatar.url
            )
        await log_channel.send(embed=log_embed)


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
    # Check if its nov 30 1:01pm manila time or later
    if not is_nov_30_101pm_or_later_manila():
        await interaction.response.send_message(
            content="The Cherry Pin system is not yet active. Please try again later.",
            ephemeral=True,
        )
        return

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

    # Build balance embed
    title_str = "Your" if member is None else f"{member.display_name}'s"
    balance_embed = discord.Embed(
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
    balance_embed.set_author(name=author_name, icon_url=author_icon_url)
    balance_embed.set_image(url=DIVIDER)

    # Build info embed
    info_embed = discord.Embed(
        title="🍒 Cherry Pin Rewards Info 🍒",
        description=(
            f"Shiny Event – 2 {CHERRY_PIN}\n"
            f"Exclusive Event – 3 {CHERRY_PIN}\n"
            f"Fishing Shiny Event (if any) – 5 {CHERRY_PIN}\n"
            f"Fishing Exclusive Event (if any) – 2 {CHERRY_PIN}\n"
            f"Legendary – 1 {CHERRY_PIN}\n"
            f"Shiny Full Odds – 2 {CHERRY_PIN}\n"
            f"Shiny Legendary Full Odds – 5 {CHERRY_PIN}\n"
            f"Fishing Legendary – 2 {CHERRY_PIN}\n"
            f"Fishing Shiny – 5 {CHERRY_PIN}\n"
        ),
        color=COLOR,
        timestamp=datetime.now(),
    )
    info_embed.set_image(url=DIVIDER)
    info_embed.set_author(name=author_name, icon_url=author_icon_url)

    user_currency_info = user_balance_cache.get(user_id, {})
    # has_box is True if at least one box is purchased
    has_box = any(
        user_currency_info.get(f"bought_{box_type}_box", "no") == "yes"
        for box_type in BOX_MAP
    )
    bought_boxes = []
    for box_type, box_data in BOX_MAP.items():
        if user_currency_info.get(f"bought_{box_type}_box", "no") == "yes":
            bought_boxes.append(f"**{box_type.title()} Box**: Purchased")
        else:
            bought_boxes.append(
                f"**{box_type.title()} Box**: Not Purchased | Quest: {box_data['quest']}"
            )

    view = Cherry_Pin_Reward_Info(
        interaction.user,
        balance_embed=balance_embed,
        info_embed=info_embed,
        has_box=has_box,
    )
    await loader.success(embed=balance_embed, content="", view=view)
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


class Cherry_Pin_Reward_Info(discord.ui.View):
    def __init__(self, user, balance_embed, info_embed, has_box, timeout=180):
        super().__init__(timeout=timeout)

        self.user = user
        self.balance_embed = balance_embed
        self.info_embed = info_embed
        self.has_box = has_box

        # Start with balance disabled
        self.balance_button.disabled = True

        # Conditionally add Box Info button
        espeon_log(
            tag="debug",
            message=f"Cherry_Pin_Reward_Info initialized for {user.name} with has_box={has_box}.",
        )
        if has_box:
            box_info_btn = discord.ui.Button(
                label="Box Info",
                emoji=Espeon_Emoji.pink_box,
                style=discord.ButtonStyle.secondary,
                custom_id="cherry_pin_box_info_button",
            )
            box_info_btn.callback = self.box_info_button_callback
            self.add_item(box_info_btn)

    # BALANCE BUTTON
    @discord.ui.button(
        label="Balance",
        emoji=CHERRY_PIN,
        style=discord.ButtonStyle.secondary,
        custom_id="cherry_pin_balance_button",
    )
    async def balance_button(self, interaction, button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't press this.", ephemeral=True
            )

        # Disable all buttons, then enable Info and Box Info (if present)
        for child in self.children:
            child.disabled = True
        self.info_button.disabled = False
        # Re-enable Box Info button if present
        for child in self.children:
            if (
                hasattr(child, "custom_id")
                and child.custom_id == "cherry_pin_box_info_button"
            ):
                child.disabled = False

        await interaction.response.edit_message(embed=self.balance_embed, view=self)

    # INFO BUTTON
    @discord.ui.button(
        label="Info",
        emoji=Espeon_Emoji.pink_flower_two,
        style=discord.ButtonStyle.secondary,
        custom_id="cherry_pin_info_button",
    )
    async def info_button(self, interaction, button):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't press this.", ephemeral=True
            )

        # Disable all buttons, then enable Balance and Box Info (if present)
        for child in self.children:
            child.disabled = True
        self.balance_button.disabled = False
        # Re-enable Box Info button if present
        for child in self.children:
            if (
                hasattr(child, "custom_id")
                and child.custom_id == "cherry_pin_box_info_button"
            ):
                child.disabled = False

        await interaction.response.edit_message(embed=self.info_embed, view=self)

    # BOX INFO BUTTON callback for manual button
    async def box_info_button_callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.user.id:
            return await interaction.response.send_message(
                "You can't press this.", ephemeral=True
            )

        if not self.has_box:
            return await interaction.response.send_message(
                "You have no boxes.", ephemeral=True
            )

        box_info_embed = discord.Embed(
            title=f"{Espeon_Emoji.pink_book} Box Quests info",
            description=(
                "- Quests can only be completed once throughout the event and can only have one winner.\n"
                "- After completing the quest, please contact a staff member, in <#1359856208961601638> to claim your prize."
            ),
            color=COLOR,
        )

        user_currency_info = user_balance_cache.get(self.user.id, {})
        for box_type, box_data in BOX_MAP.items():
            if user_currency_info.get(f"bought_{box_type}_box") == "yes":
                box_info_embed.add_field(
                    name=f"{Espeon_Emoji.pink_box} {box_type.title()} Box",
                    value=f"- {Espeon_Emoji.pink_cherry} **Quest:** {box_data['quest']}",
                    inline=False,
                )
        guild = interaction.guild
        # box_info_embed.set_image(url=DIVIDER)
        box_info_embed.set_footer(
            text="Not every wonder is meant to be shared.", icon_url=guild.icon.url
        )

        await interaction.response.send_message(embed=box_info_embed, ephemeral=True)
