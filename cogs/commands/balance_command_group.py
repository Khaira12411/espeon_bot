from typing import Literal, Optional, Union

import discord
from discord import app_commands
from discord.ext import commands
from config.current_setup import STRAYMONS_GUILD_ID
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *
from utils.group_func.server_currency.balance_func import (
    add_balance_func,
    remove_balance_func,
    reset_balance_func,
    view_balance_func,
)


# 🟣────────────────────────────────────────────
#           💜 Balance Cog Setup 💜
# ─────────────────────────────────────────────
class Balance_Group_Command(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #           💜 Slash Command Group 💜
    # 🟣────────────────────────────────────────────
    balance_group = app_commands.Group(
        name="balance",
        description="Commands related to server currency balance",
    )

    # 🟣────────────────────────────────────────────
    #           💜 /balance view 💜
    # ─────────────────────────────────────────────
    @balance_group.command(
        name="view",
        description="View your balance, or (staff only) another user's balance",
    )
    @app_commands.describe(
        member="(Staff only) The member to view the balance of",
    )
    async def view_balance(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
    ):
        slash_cmd_name = "balance view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=view_balance_func,
            member=member,
        )

    view_balance.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /balance add 💜
    # 🟣────────────────────────────────────────────
    @balance_group.command(name="add", description="Add balance to a user's account")
    @app_commands.describe(
        member="The member to add balance to",
        amount="The amount of balance to add",
    )
    @clan_staff_only()
    async def add_balance(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
    ):
        slash_cmd_name = "balance add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=add_balance_func,
            member=member,
            amount=amount,
        )

    add_balance.extras = {"category": "Staff"}

    # 🟣────────────────────────────────────────────
    #           💜 /balance remove 💜
    # 🟣────────────────────────────────────────────
    @balance_group.command(
        name="remove", description="Remove balance from a user's account"
    )
    @app_commands.describe(
        member="The member to remove balance from",
        amount="The amount of balance to remove",
    )
    @clan_staff_only()
    async def remove_balance(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        amount: int,
    ):
        slash_cmd_name = "balance remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=remove_balance_func,
            member=member,
            amount=amount,
        )

    remove_balance.extras = {"category": "Staff"}

    # 🟣────────────────────────────────────────────
    #           💜 /balance reset 💜
    # ─────────────────────────────────────────────
    @balance_group.command(
        name="reset", description="Reset a user's or all users' balances to zero"
    )
    @app_commands.describe(
        member="The member to reset the balance of",
        all_users="Reset the balance for all users in the server",
    )
    @owner_only()
    async def reset_balance(
        self,
        interaction: discord.Interaction,
        member: Optional[discord.Member] = None,
        all_users: Literal["Yes", "No"] = None,
    ):
        slash_cmd_name = "balance reset"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=reset_balance_func,
            member=member,
            all_users=all_users,
        )

    reset_balance.extras = {"category": "Staff"}


async def setup(bot: commands.Bot):
    await bot.add_cog(Balance_Group_Command(bot))
