# cogs/weakness_cog.py
import discord
from discord import app_commands
from discord.ext import commands

from utils.essentials.pokemon_autocomplete import pokemon_autocomplete
from utils.visuals.embeds.visual_helpers import (
    design_embed,
    format_bulletin_desc,
    pokemon_embed,
)
from utils.visuals.embeds.weakness_embed import build_weakness_embed_from_input


# -------------------- Weakness Cog --------------------
class Weakness(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="test-weakness", description="Show a Pokémon's type weaknesses"
    )
    @app_commands.describe(pokemon="The Pokémon name or dex number")
    @app_commands.autocomplete(pokemon=pokemon_autocomplete)  # 👈 attach autocomplete
    async def test_weakness(self, interaction: discord.Interaction, pokemon: str):
        # pokemon here is already the Choice.value you set in autocomplete
        print(pokemon)
        embed = build_weakness_embed_from_input(pokemon)

        if not embed:
            await interaction.response.send_message(
                f"❌ Pokémon `{pokemon}` not found in weakness chart.",
                ephemeral=True,
            )
            return
        embed = await pokemon_embed(embed=embed, pokemon_name=pokemon)
        await interaction.response.send_message(embed=embed)

    test_weakness.extras = {"category": "Public"}


# -------------------- Setup --------------------
async def setup(bot: commands.Bot):
    await bot.add_cog(Weakness(bot))
