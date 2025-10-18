import discord
from discord import app_commands
from discord.ext import commands


class ViewCacheSize(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="view-cache-size", description="Show the size of key caches and indexes"
    )
    async def view_cache_size_slash(self, interaction: discord.Interaction):
        from utils.cache.market_alert_cache import (
            _market_alert_index,
            market_alert_cache,
        )
        from utils.cache.mr_weakness_cache import mr_weakness_user_cache

        try:
            ev_tracker_cache = None
            try:
                from utils.cache.ev_tracker_cache import ev_tracker_cache
            except ImportError:
                pass
            # Import caches from pokemon_autocomplete.py
            from utils.essentials.pokemon_autocomplete import (
                DEX_TO_KEY,
                KEY_NORMALIZED,
                POKEMON_LIST,
                POKEMON_NORMALIZED,
                WEAKNESS_CHART,
            )

            msg = ["**Cache Sizes:**"]
            msg.append(f"Market Alert Cache: {len(market_alert_cache)} entries")
            msg.append(f"Market Alert Index: {len(_market_alert_index)} keys")
            msg.append(f"Mr. Weakness User Cache: {len(mr_weakness_user_cache)} users")
            if ev_tracker_cache is not None:
                msg.append(f"EV Tracker Cache: {len(ev_tracker_cache)} users")
            # Add pokemon_autocomplete caches
            msg.append(f"WEAKNESS_CHART: {len(WEAKNESS_CHART)} entries")
            msg.append(f"DEX_TO_KEY: {len(DEX_TO_KEY)} keys")
            msg.append(f"KEY_NORMALIZED: {len(KEY_NORMALIZED)} keys")
            msg.append(f"POKEMON_LIST: {len(POKEMON_LIST)} entries")
            msg.append(f"POKEMON_NORMALIZED: {len(POKEMON_NORMALIZED)} entries")
            await interaction.response.send_message("\n".join(msg))
        except Exception as e:
            await interaction.response.send_message(f"Error: {e}")


async def setup(bot):
    await bot.add_cog(ViewCacheSize(bot))
