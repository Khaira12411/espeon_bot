import discord
from discord import app_commands
from discord.ext import commands

from config.current_setup import CC_GUILD_ID, STRAYMONS_GUILD_ID
from utils.essentials.command_safe import run_command_safe
from utils.essentials.pokemon_autocomplete import *
from utils.essentials.role_checks import *
from utils.group_func.promo import *
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 🪻────────────────────────────────────────────
#           ✨ Promo Cog Setup ✨
# ─────────────────────────────────────────────
class PromoGroup(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🪻────────────────────────────────────────────
    #           ✨ Slash Command Group ✨
    # 🪻────────────────────────────────────────────
    promo_group = app_commands.Group(
        name="promo",
        description="Commands related to clan promo events",
    )

    # 🪻────────────────────────────────────────────
    #           ✨ /promo add✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="add", description="Add a new clan promo event")
    @app_commands.describe(
        name="Name of the promo event",
        prize="Prize for the promo event",
        catch_rate="Catch rate for the promo event (e.g., 1/50)",
        battle_rate="Battle rate for the promo event (e.g., 1/50)",
        fish_rate="Fishing rate for the promo event (e.g., 1/50)",
        emoji="Emoji to represent the promo event",
        whitelist_role_id="Role ID to whitelist for this promo event (optional)",
        image_url="URL of the image to display in the promo embed (optional)",
        duration="Duration of the promo event in hours (optional)",
    )
    @clan_staff_only()  # 👈 restrict to clan staff
    async def add_promo(
        self,
        interaction: discord.Interaction,
        name: str,
        prize: str,
        catch_rate: str,
        battle_rate: str,
        fish_rate: str,
        emoji: str,
        whitelist_role_id: int = None,
        image_url: str = None,
        duration: str = None,
    ):
        slash_cmd_name = "promo add"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=add_promo_func,
                name=name,
                prize=prize,
                catch_rate=catch_rate,
                battle_rate=battle_rate,
                fish_rate=fish_rate,
                emoji=emoji,
                whitelist_role_id=whitelist_role_id,
                image_url=image_url,
                duration=duration,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo add command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e

    add_promo.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /promo edit✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="edit", description="Edit an existing clan promo event")
    @app_commands.describe(
        prize="New prize for the promo event (optional)",
        catch_rate="New catch rate for the promo event (optional)",
        battle_rate="New battle rate for the promo event (optional)",
        fish_rate="New fishing rate for the promo event (optional)",
        emoji="New emoji to represent the promo event (optional)",
        whitelist_role_id="New role ID to whitelist for this promo event (optional)",
        image_url="New URL of the image to display in the promo embed (optional)",
        duration="New duration of the promo event in hours (optional)",
    )
    @clan_staff_only()  # 👈 restrict to clan staf
    async def edit_promo(
        self,
        interaction: discord.Interaction,
        prize: str = None,
        catch_rate: str = None,
        battle_rate: str = None,
        fish_rate: str = None,
        emoji: str = None,
        whitelist_role_id: int = None,
        image_url: str = None,
        duration: str = None,
    ):
        slash_cmd_name = "promo edit"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=edit_promo_func,
                prize=prize,
                catch_rate=catch_rate,
                battle_rate=battle_rate,
                fish_rate=fish_rate,
                emoji=emoji,
                whitelist_role_id=whitelist_role_id,
                image_url=image_url,
                duration=duration,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo edit command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e
    edit_promo.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /promo cancel✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="cancel", description="Cancel an existing clan promo event")
    @clan_staff_only()  # 👈 restrict to clan staff
    async def cancel_promo(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "promo cancel"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=cancel_promo_func,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo cancel command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e
    cancel_promo.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /promo end✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="end", description="End an existing clan promo event")
    @clan_staff_only()  # 👈 restrict to clan staff
    async def end_promo(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "promo end"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=end_promo_func,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo end command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e
    end_promo.extras = {"category": "Staff"}

    # 🪻────────────────────────────────────────────
    #           ✨ /promo view✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="view", description="View the current clan promo event")
    async def view_promo(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "promo view"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=view_promo_func,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo view command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e
    view_promo.extras = {"category": "Public"}

    # 🪻────────────────────────────────────────────
    #           ✨ /promo leaderboard✨
    # 🪻────────────────────────────────────────────
    @promo_group.command(name="leaderboard", description="View the leaderboard for the current clan promo event")
    async def promo_leaderboard(
        self,
        interaction: discord.Interaction,
    ):
        slash_cmd_name = "promo leaderboard"
        try:
            await run_command_safe(
                bot=self.bot,
                interaction=interaction,
                slash_cmd_name=slash_cmd_name,
                command_func=promo_item_leaderboard_func,
            )
        except Exception as e:
            espeon_log.error(
                f"Error in /promo leaderboard command: {e}",
                context=EspeonContext(
                    bot=self.bot,
                    interaction=interaction,
                    slash_cmd_name=slash_cmd_name,
                ),
            )
            raise e
    promo_leaderboard.extras = {"category": "Public"}

# 🪻────────────────────────────────────────────
#           ✨ Cog Setup Function ✨
# ─────────────────────────────────────────────
async def setup(bot: commands.Bot):
    await bot.add_cog(PromoGroup(bot))