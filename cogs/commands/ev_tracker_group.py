# 🟣────────────────────────────────────────────
#           💜 EV Tracker Command Group 💜
# ─────────────────────────────────────────────
import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.command_group_counter import *
from utils.essentials.command_safe import run_command_safe
from utils.essentials.role_checks import *
from utils.group_func.ev_tracker import *


# 🟣────────────────────────────────────────────
#           💜 EV Tracker Cog Setup 💜
# ─────────────────────────────────────────────
class EvTrackerGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🟣────────────────────────────────────────────
    #           💜 Slash Command Group 💜
    # 🟣────────────────────────────────────────────
    ev_tracker_group = app_commands.Group(
        name="ev-tracker", description="Commands related to EV Tracker"
    )

    # 🟣────────────────────────────────────────────
    #           💜 /ev-tracker add 💜
    # 🟣────────────────────────────────────────────
    @ev_tracker_group.command(
        name="add",
        description="Start tracking EVs for a Pokemon (one mon at a time)",
    )
    @espeon_roles_only()
    @app_commands.describe(
        pokemon="Name of the Pokemon you want to track (required)",
        hp="Current/goal HP EVs (e.g., 0/252) to start tracking",
        atk="Current/goal Attack EVs (e.g., 0/252) to start tracking",
        spa="Current/goal Special Attack EVs (e.g., 0/252) to start tracking",
        def_="Current/goal Defense EVs (e.g., 0/252) to start tracking",
        spd="Current/goal Special Defense EVs (e.g., 0/252) to start tracking",
        spe="Current/goal Speed EVs (e.g., 0/252) to start tracking",
    )
    async def ev_tracker_add(
        self,
        interaction: discord.Interaction,
        pokemon: str,
        hp: str = None,
        atk: str = None,
        spa: str = None,
        def_: str = None,
        spd: str = None,
        spe: str = None,
    ):
        slash_cmd_name = "ev-tracker track"
        # Pass everything to the brain function
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=ev_tracker_add_func,
            pokemon=pokemon,
            hp=hp,
            atk=atk,
            spa=spa,
            def_=def_,
            spd=spd,
            spe=spe,
        )

    ev_tracker_add.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /ev-tracker view 💜
    # 🟣────────────────────────────────────────────
    @ev_tracker_group.command(
        name="view",
        description="View your current EV tracker",
    )
    @espeon_roles_only()
    async def ev_tracker_view(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "ev-tracker view"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=ev_tracker_view_func,
        )

    ev_tracker_view.extras = { "category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /ev-tracker update 💜
    # 🟣────────────────────────────────────────────
    @ev_tracker_group.command(
        name="update",
        description="Add or update EVs for your current tracked Pokémon",
    )
    @espeon_roles_only()
    @app_commands.describe(
        hp="Current/goal HP EVs (e.g., 0/252)",
        atk="Current/goal Attack EVs (e.g., 0/252)",
        spa="Current/goal Special Attack EVs (e.g., 0/252)",
        def_="Current/goal Defense EVs (e.g., 0/252)",
        spd="Current/goal Special Defense EVs (e.g., 0/252)",
        spe="Current/goal Speed EVs (e.g., 0/252)",
    )
    async def ev_tracker_update(
        self,
        interaction: discord.Interaction,
        hp: str = None,
        atk: str = None,
        spa: str = None,
        def_: str = None,
        spd: str = None,
        spe: str = None,
    ):
        slash_cmd_name = "ev-tracker update"
        # Pass everything to the brain function
        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=ev_tracker_update_func,  # we'll create this brain function
            hp=hp,
            atk=atk,
            spa=spa,
            def_=def_,
            spd=spd,
            spe=spe,
        )

    ev_tracker_update.extras = {"category": "Public"}

    # 🟣────────────────────────────────────────────
    #           💜 /ev-tracker reset 💜
    # 🟣────────────────────────────────────────────
    @ev_tracker_group.command(
        name="reset",
        description="Removes your current EV tracker",
    )
    @espeon_roles_only()
    async def ev_tracker_reset(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "ev-tracker reset"

        await run_command_safe(
            bot=self.bot,
            interaction=interaction,
            slash_cmd_name=slash_cmd_name,
            command_func=ev_tracker_reset_func,
        )

    ev_tracker_reset.extras = {"category": "Public"}


# 🟣────────────────────────────────────────────
#           💜 Cog Setup Function 💜
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    cog = EvTrackerGroup(bot)
    await bot.add_cog(cog)
    ev_tracker_group = EvTrackerGroup.ev_tracker_group  # top-level app_commands.Group
    await log_command_group_full_paths_to_cache(bot=bot, group=ev_tracker_group)
