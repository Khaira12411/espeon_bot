# 🟣────────────────────────────────────────────
#           💜 Timer Command Group 💜
# ─────────────────────────────────────────────
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *
from utils.group_func.timer import *


# 🟣────────────────────────────────────────────
#           💜 Timer Command Group Cog Setup 💜
# ─────────────────────────────────────────────
class TimerGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #           💜 Slash Command Group 💜
    # 🟣────────────────────────────────────────────
    timer_group = app_commands.Group(
        name="timer", description="Commands related to Timer"
    )

    # 🟣────────────────────────────────────────────
    #           💜 /timer pokemon-set 💜
    # 🟣────────────────────────────────────────────
    @timer_group.command(
        name="pokemon-set",
        description="Sets or removes your pokemon command timer",
    )
    @espeon_roles_only()
    async def timer_pokemon_set(
        self,
        interaction: discord.Interaction,
        mode: Literal["On", "On w/o pings", "React", "Off"],
    ):
        slash_cmd_name = "timer pokemon-set"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=timer_pokemon_set_func,
            mode=mode,
        )

    timer_pokemon_set.extras = {"category": "Owner"}

    # 🟣────────────────────────────────────────────
    #           💜 /timer pokemon-view 💜
    # 🟣────────────────────────────────────────────
    @timer_group.command(
        name="pokemon-view",
        description="Views your current pokemon timer settings",
    )
    @espeon_roles_only()
    async def timer_pokemon_view(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "timer pokemon-view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=timer_pokemon_view_func,
        )

    timer_pokemon_view.extras = {"category": "Owner"}


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = TimerGroup(bot)
    await bot.add_cog(cog)
    timer_group = TimerGroup.timer_group  # top-level app_commands.Group
    await log_command_group_full_paths_to_cache(bot=bot, group=timer_group)
