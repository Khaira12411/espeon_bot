# 🟣✨───────────────────────────────────────────
#           Imports for AFK Group 🌞
# ─────────────────────────────────────────────
from typing import Literal
import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *
from utils.group_func.afk import *

# 🟡☀️───────────────────────────────────────────
#          AFK Command Group Cog Setup 🟣💜
# ─────────────────────────────────────────────
class AFK_Command_Group(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣🔮─────────────────────────────────────────
    #           AFK Command Group 🟡🌟
    # ─────────────────────────────────────────────
    afk_group = app_commands.Group(
        name="afk", description="AFK Group Commands"
    )

    # 🟡🌻─────────────────────────────────────────
    #     /afk set 🟣💫
    # ─────────────────────────────────────────────
    @afk_group.command(name="set", description="Sets an AFK status")
    @app_commands.describe(
        reason="Your AFK reason",
    )
    async def afk_set(self, interaction: discord.Interaction, reason: str):
        slash_cmd_name = "afk set"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=afk_set_func,
            reason=reason,
        )

    afk_set.extras = {"category": "Public"}

    # 🟡🌻─────────────────────────────────────────
    #     /afk update 🟣💫
    # ─────────────────────────────────────────────
    @afk_group.command(name="update", description="Updates your AFK reason")
    @app_commands.describe(
        reason="Your new AFK reason",
    )
    async def afk_update(self, interaction: discord.Interaction, reason: str):
        slash_cmd_name = "afk update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=afk_update_func,
            reason=reason,
        )

    afk_update.extras = {"category": "Public"}

    # 🟡🌻─────────────────────────────────────────
    #     /afk remove 🟣💫
    # ─────────────────────────────────────────────
    @afk_group.command(name="remove", description="Removes your AFK Status")
    async def afk_remove(self, interaction: discord.Interaction):
        slash_cmd_name = "afk remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=afk_remove_func,
        )

    afk_remove.extras = {"category": "Public"}

# 🟣🌙───────────────────────────────────────────
#     AFK Group Command Cog Setup Function 🟡☀️
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = AFK_Command_Group(bot)
    await bot.add_cog(cog)
    afk_group = AFK_Command_Group.afk_group
    await log_command_group_full_paths_to_cache(bot=bot, group=afk_group)
