from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Button, View

from config.aesthetic import Espeon_Emoji
from config.current_setup import KHY_USER_ID, STRAYMONS_GUILD_ID
from config.petal_lace_settings import (COLOR, DIVIDER, LEADERBOARD_THUMBNAIL,
                                        SERVER_CURRENCY_EMOJI,
                                        SERVER_CURRENCY_NAME)
from config.straymons_constants import (STRAYMONS__ROLES,
                                        STRAYMONS__TEXT_CHANNELS)
from utils.cache.cache_list import server_shop_cache, user_balance_cache
from utils.database.server_currency import fetch_all_user_balances
from utils.essentials.loader import pretty_defer
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 🌸───────────────────────────────────────────────🌸
# 🩷 ⏰ PAGINATED LEADERBOARD VIEW       🩷
# 🌸───────────────────────────────────────────────🌸
class Leaderboard_Paginator(View):
    def __init__(self, bot, user, sorted_balances, per_page=10, timeout=120):
        super().__init__(timeout=timeout)
        self.bot = bot
        self.user = user
        self.sorted_balances = sorted_balances
        self.per_page = per_page
        self.page = 0
        self.max_page = (len(sorted_balances) - 1) // per_page
        self.message: discord.Message | None = None  # Store the sent message

        # If only one page, remove all buttons
        if self.max_page == 0:
            self.clear_items()

    @discord.ui.button(
        emoji=Espeon_Emoji.left_arrow, style=discord.ButtonStyle.secondary
    )
    async def previous_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page -= 1
        if self.page < 0:
            self.page = self.max_page
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    @discord.ui.button(
        emoji=Espeon_Emoji.right_arrow, style=discord.ButtonStyle.secondary
    )
    async def next_page(self, interaction: discord.Interaction, button: Button):
        if interaction.user.id != self.user.id:
            await interaction.response.send_message(
                "You can't press this button.", ephemeral=True
            )
            return
        self.page += 1
        if self.page > self.max_page:
            self.page = 0
        await self.update_buttons(interaction)
        await interaction.response.edit_message(embed=await self.get_embed(), view=self)

    async def update_buttons(self, interaction):
        # Disable left arrow on first page, enable otherwise
        for item in self.children:
            if (
                hasattr(item, "callback")
                and getattr(item.callback, "__name__", "") == "previous_page"
            ):
                item.disabled = self.page == 0
            if (
                hasattr(item, "callback")
                and getattr(item.callback, "__name__", "") == "next_page"
            ):
                item.disabled = self.page == self.max_page
        await interaction.message.edit(view=self)

    async def get_embed(self):
        start_index = self.page * self.per_page
        end_index = start_index + self.per_page
        page_balances = self.sorted_balances[start_index:end_index]

        description_lines = []
        rank_offset = start_index + 1
        title = f"{SERVER_CURRENCY_EMOJI} {SERVER_CURRENCY_NAME} Leaderboard "
        embed = discord.Embed(title=title, color=COLOR)
        embed.set_thumbnail(url=LEADERBOARD_THUMBNAIL)
        embed.set_image(url=DIVIDER)
        straymon_guild = self.bot.get_guild(STRAYMONS_GUILD_ID)
        total_users = len(self.sorted_balances)
        embed.set_footer(
            icon_url=(
                straymon_guild.icon.url
                if straymon_guild and straymon_guild.icon
                else None
            ),
            text=f"Page {self.page + 1} of {self.max_page + 1} | Total Users: {total_users}",
        )
        for i, (user_id, balance) in enumerate(page_balances, start=rank_offset):
            user = self.bot.get_user(user_id)
            username = user.display_name
            field_name = f"{i}. {username}"
            if i == 1:
                field_name = f"🥇 {username}"
            elif i == 2:
                field_name = f"🥈 {username}"
            elif i == 3:
                field_name = f"🥉 {username}"

            field_value = f"{balance:,} {SERVER_CURRENCY_EMOJI}"
            embed.add_field(name=field_name, value=f"> - {field_value}", inline=False)
        return embed

    async def on_timeout(self):
        # Disable all buttons on timeout
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except (discord.NotFound, discord.HTTPException):
                pass


async def balance_leaderboard_func(
    bot: commands.Bot,
    interaction: discord.Interaction,
):
    """
    Shows the balance leaderboard
    """

    # Defer
    loader = await pretty_defer(
        interaction=interaction,
        content="Loading leaderboard...",
        ephemeral=False,
    )

    # Fetch all user balances
    user_balances = await fetch_all_user_balances(bot)
    if not user_balances:
        await loader.error(
            content="No user server currency balances found.",
        )
        return

    # Filter out users with zero balance and sort by highest balance first
    sorted_balances = [
        (row["user_id"], row["cherry_pin_balance"])
        for row in user_balances
        if row["cherry_pin_balance"] > 0
    ]
    sorted_balances.sort(key=lambda x: x[1], reverse=True)

    # Create paginator
    paginator = Leaderboard_Paginator(
        bot=bot,
        user=interaction.user,
        sorted_balances=sorted_balances,
        per_page=10,
        timeout=120,
    )
    embed = await paginator.get_embed()
    sent_message = await loader.success(
        content="",
        embed=embed,
        view=paginator,
    )
    paginator.message = sent_message

