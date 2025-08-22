# cogs/mr_weakness.py
import discord
from discord.ext import commands
from discord import app_commands

from utils.loggers.espeon_log import espeon_log, EspeonContext
from utils.cache.mr_weakness_cache import mr_weakness_user_cache
from utils.group_func.mr_weakness.mr_weakness_db_func import (
    fetch_all_mr_user_settings,
    upsert_mr_user_setting,
)


class MrWeaknessCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # 🛠️────────────────────────────────────────────
    #            /mr-weakness-toggle
    # 🛠️────────────────────────────────────────────
    @app_commands.command(
        name="mr-weakness-toggle",
        description="Choose how Mr. Weakness displays Pokémon weaknesses: Off, Truncated, or Full.",
    )
    @app_commands.choices(
        settings=[
            app_commands.Choice(name="Off 🚫", value="off"),
            app_commands.Choice(name="Truncated ✂️", value="truncated"),
            app_commands.Choice(name="Full 📜", value="full"),
        ]
    )
    async def mr_weakness_toggle(
        self, interaction: discord.Interaction, settings: app_commands.Choice[str]
    ):
        user_id = interaction.user.id
        choice = settings.value

        # 🚫 Handle "Off"
        if choice == "off":
            if user_id in mr_weakness_user_cache:
                mr_weakness_user_cache.pop(user_id)
            await upsert_mr_user_setting(self.bot, user_id, "off")

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
        mr_weakness_user_cache[user_id] = choice
        await upsert_mr_user_setting(self.bot, user_id, choice)

        if choice == "truncated":
            msg = "✂️ **Truncated mode enabled.**\nOnly **major weaknesses (4× and 2×)** will be displayed."
        else:  # full
            msg = "📜 **Full mode enabled.**\nYou’ll see the **complete weakness chart** (all multipliers)."

        await interaction.response.send_message(msg, ephemeral=True)
        espeon_log(
            "ready",
            f"User {user_id} set Mr. Weakness alerts to {choice}",
            context=EspeonContext.STRAYMONS,
        )

    # 🕵️────────────────────────────────────────────
    #            /mr-weakness-view
    # 🕵️────────────────────────────────────────────
    @app_commands.command(
        name="mr-weakness-view",
        description="View your current Mr. Weakness display setting.",
    )
    async def mr_weakness_view(self, interaction: discord.Interaction):
        user_id = interaction.user.id
        current = mr_weakness_user_cache.get(user_id, "off")

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


async def setup(bot: commands.Bot):
    await bot.add_cog(MrWeaknessCog(bot))
