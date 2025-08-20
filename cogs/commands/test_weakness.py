# cogs/weakness_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from utils.visuals.embeds.weakness_embed import build_weakness_embed_from_input


# -------------------- Weakness Cog --------------------
class Weakness(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="test-weakness", description="Show a Pokémon's type weaknesses"
    )
    @app_commands.describe(pokemon="The Pokémon name or dex number")
    async def test_weakness(self, interaction: discord.Interaction, pokemon: str):
        # ⚡ Single call: resolve input and build embed
        embed = build_weakness_embed_from_input(pokemon)

        if not embed:
            await interaction.response.send_message(
                f"❌ Pokémon `{pokemon}` not found in weakness chart."
            )
            return

        await interaction.response.send_message(embed=embed)


# -------------------- Setup --------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Weakness(bot))
