# 🟣────────────────────────────────────────────
#           💜 WB Command Group 💜
# ─────────────────────────────────────────────
from typing import Literal

import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *
from utils.group_func.wb_sub import *
from utils.group_func.wb_sub.wb_sub_db_func import wb_sub_autocomplete

# 🧠 List of known boss names for autocomplete
BOSS_NAMES = [
    "Alcremie",
    "Appletun",
    "Blastoise",
    "Butterfree",
    "Centiskorch",
    "Charizard",
    "Cinderace",
    "Coalossal",
    "Copperajah",
    "Corviknight",
    "Drednaw",
    "Duraludon",
    "Eevee",
    "Eternatus",
    "Flapple",
    "Garbodor",
    "Gengar",
    "Grimmsnarl",
    "Hatterene",
    "Inteleon",
    "Kingler",
    "Lapras",
    "Machamp",
    "Melmetal",
    "Meowth",
    "Orbeetle",
    "Pikachu",
    "Rillaboom",
    "Sandaconda",
    "Snorlax",
    "Toxtricity",
    "Urshifu-RapidStrike",
    "Urshifu-SingleStrike",
    "Venusaur",
]


# 🔍 Boss name autocomplete function
async def autocomplete_boss_name(
    interaction: discord.Interaction, current: str
) -> list[app_commands.Choice[str]]:
    current = current.lower()
    matches = [name for name in BOSS_NAMES if current in name.lower()]
    return [app_commands.Choice(name=match, value=match) for match in matches[:25]]


# 🟣────────────────────────────────────────────
#           💜 WB Command Group Cog Setup 💜
# ─────────────────────────────────────────────
class WBSUBGROUP(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #           💜 Slash Command Group 💜
    # 🟣────────────────────────────────────────────
    wb_sub_group = app_commands.Group(
        name="wb-sub", description="Commands related to World Boss Subscription Pings"
    )

    # 🟣────────────────────────────────────────────
    #           💜 /wb-sub add 💜
    # 🟣────────────────────────────────────────────
    @wb_sub_group.command(
        name="add",
        description="Add a specific World Boss subscription ping",
    )
    @app_commands.autocomplete(boss_name=autocomplete_boss_name)
    @app_commands.describe(
        boss_name="The boss name",
        variant="Regular, Shiny or Both",
        mode="How to notify you?",
    )
    @espeon_roles_only()
    async def wb_sub_add(
        self,
        interaction: discord.Interaction,
        boss_name: str,
        variant: Literal["Regular", "Shiny", "Both"],
        mode: Literal["DM", "Channel"],
    ):
        slash_cmd_name = "wb-sub add"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=wb_sub_add_func,
            boss_name=boss_name,
            variant=variant,
            mode=mode,
        )

    wb_sub_add.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /wb-sub remove 💜
    # 🟣────────────────────────────────────────────
    @wb_sub_group.command(
        name="remove",
        description="Removes a specific World Boss subscription ping or all of your subscription ping",
    )
    @app_commands.autocomplete(boss_name=wb_sub_autocomplete)
    @app_commands.describe(
        boss_name="The boss to remove subscription pings from, put all to remove all",
    )
    @espeon_roles_only()
    async def wb_sub_remove(
        self,
        interaction: discord.Interaction,
        boss_name: str,
    ):
        slash_cmd_name = "wb-sub remove"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=wb_sub_remove_func,
            boss_name=boss_name,
        )

    wb_sub_remove.extras = {"category": "Public"}
    # 🟣────────────────────────────────────────────
    #           💜 /wb-sub update 💜
    # 🟣────────────────────────────────────────────
    @wb_sub_group.command(
        name="update",
        description="Updates a specific World Boss subscription ping",
    )
    @app_commands.autocomplete(boss_name=wb_sub_autocomplete)
    @app_commands.describe(
        boss_name="The boss name",
        new_variant="Regular, Shiny or Both",
        new_mode="How to notify you?",
    )
    @espeon_roles_only()
    async def wb_sub_update(
        self,
        interaction: discord.Interaction,
        boss_name: str,
        new_variant: Literal["Regular", "Shiny", "Both"],
        new_mode: Literal["DM", "Channel"],
    ):
        slash_cmd_name = "wb-sub update"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=wb_sub_update_func,
            boss_name=boss_name,
            new_variant=new_variant,
            new_mode=new_mode,
        )

    wb_sub_update.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /wb-sub view 💜
    # 🟣────────────────────────────────────────────
    @wb_sub_group.command(
        name="view",
        description="Views your current World Boss subscription ping",
    )
    @espeon_roles_only()
    async def wb_view(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "wb-sub view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=wb_view_func,
        )

    wb_view.extras = {"category": "Public"}


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = WBSUBGROUP(bot)
    await bot.add_cog(cog)
    wb_sub_group = WBSUBGROUP.wb_sub_group  # top-level app_commands.Group
    await log_command_group_full_paths_to_cache(bot=bot, group=wb_sub_group)
