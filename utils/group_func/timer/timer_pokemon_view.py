# 🟣────────────────────────────────────────────
#        Timer Pokémon View Function
# 🟣────────────────────────────────────────────

import discord
from discord.ext import commands

from utils.group_func.timer.timer_db_func import fetch_timer
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.visual_helpers import set_embed_user_context


async def timer_pokemon_view_func(bot: commands.Bot, interaction: discord.Interaction):
    """
    Show the user's current Pokémon timer settings in a cute embed.
    """
    user = interaction.user
    user_id = user.id

    # Fetch user's timer settings from DB
    timer_data = await fetch_timer(bot, user_id)
    if not timer_data:
        timer_data = {"pokemon_setting": "Not set yet"}

    pokemon_setting = timer_data.get("pokemon_setting", "Not set yet")

    # 🌸 Build embed
    embed = discord.Embed(
        title="💜 Current Timer Settings",
        description=f"Pokémon: **{pokemon_setting.title()}**",
        color=0x9B59B6,  # purple Wooper color
    )
    embed = set_embed_user_context(embed=embed, user=user)

    # Send ephemeral interaction response
    try:
        await interaction.response.send_message(embed=embed, ephemeral=True)
        espeon_log(
            tag="info",
            message=f"Displayed Pokémon timer settings for user {user_id}: {pokemon_setting}",
            context=EspeonContext.STRAYMONS,
        )
    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Failed to send Pokémon timer view for user {user_id}: {e}",
            context=EspeonContext.STRAYMONS,
        )
