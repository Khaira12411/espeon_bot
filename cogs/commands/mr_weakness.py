# cogs/mr_weakness.py
import discord
from discord import app_commands
from discord.ext import commands

from utils.cache.mr_weakness_cache import (
    mr_weakness_user_cache,
    insert_mr_user,
    remove_mr_user,
    get_mr_user,
)
from utils.essentials.role_checks import espeon_roles_only
from utils.group_func.mr_weakness.mr_weakness_db_func import upsert_mr_user_setting
from utils.loggers.espeon_log import EspeonContext, espeon_log


class MrWeaknessCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🛠️────────────────────────────────────────────
    #            /mr-weakness-toggle
    # 🛠️────────────────────────────────────────────
    @app_commands.command(
        name="mr-weakness-toggle",
        description="Choose how Meowrogue Weakness displays Pokemon weaknesses: Off, Truncated, or Full.",
    )
    @app_commands.choices(
        settings=[
            app_commands.Choice(name="Off 🚫", value="off"),
            app_commands.Choice(name="Truncated ✂️", value="truncated"),
            app_commands.Choice(name="Full 📜", value="full"),
        ]
    )
    @espeon_roles_only()
    async def mr_weakness_toggle(
        self, interaction: discord.Interaction, settings: app_commands.Choice[str]
    ):
        user_id = interaction.user.id
        choice = settings.value

        # 🚫 Handle "Off"
        if choice == "off":
            remove_mr_user(user_id)  # update cache
            await upsert_mr_user_setting(self.bot, user_id, "off")  # update DB

            await interaction.response.send_message(
                "🚫 **Mr. Weakness disabled.**\nYou will no longer see weakness alerts.",
                ephemeral=True,
            )
            espeon_log(
                "ready",
                f"User {user_id} turned OFF Mr. Weakness alerts",
                context=EspeonContext.STRAYMONS,
            )
            return

        # ✂️ / 📜 Handle "Truncated" or "Full"
        insert_mr_user(user_id, choice)  # insert or update cache
        await upsert_mr_user_setting(self.bot, user_id, choice)  # update DB

        msg = (
            "✂️ **Truncated mode enabled.**\nOnly **major weaknesses (4× and 2×)** will be displayed."
            if choice == "truncated"
            else "📜 **Full mode enabled.**\nYou’ll see the **complete weakness chart** (all multipliers)."
        )

        await interaction.response.send_message(msg, ephemeral=True)
        espeon_log(
            "ready",
            f"User {user_id} set Mr. Weakness alerts to {choice}",
            context=EspeonContext.STRAYMONS,
        )

    mr_weakness_toggle.extras = {"category": "Public"}

    # 🕵️────────────────────────────────────────────
    #            /mr-weakness-view
    # 🕵️────────────────────────────────────────────
    @app_commands.command(
        name="mr-weakness-view",
        description="View your current Meowrogue Weakness display setting.",
    )
    @espeon_roles_only()
    async def mr_weakness_view(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current = get_mr_user(user_id) or "off"  # only read from cache

        if current == "off":
            msg = "🚫 **Mr. Weakness is currently disabled.**"
        elif current == "truncated":
            msg = "✂️ **Truncated mode is active.**\nOnly **major weaknesses (4× and 2×)** are shown."
        else:  # full
            msg = "📜 **Full mode is active.**\nYou’ll see the **complete weakness chart** (all multipliers)."

        await interaction.response.send_message(msg, ephemeral=True)
        espeon_log(
            "ready",
            f"User {user_id} viewed their Mr. Weakness setting: {current}",
            context=EspeonContext.STRAYMONS,
        )

    mr_weakness_view.extras = {"category": "Public"}


async def setup(bot: commands.Bot):
    await bot.add_cog(MrWeaknessCog(bot))
