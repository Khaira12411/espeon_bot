import tracemalloc

import discord
from discord.ext import commands


class MemoryUsage(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="memoryusage")
    async def memory_usage(self, ctx):
        """Report top memory usage lines using tracemalloc."""
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        lines = [f"[ Top 10 memory usage ]"]
        for stat in top_stats[:10]:
            lines.append(str(stat))
        await ctx.send("\n".join(lines))

    @discord.app_commands.command(
        name="memoryusage", description="Show top memory usage lines (tracemalloc)"
    )
    async def memory_usage_slash(self, interaction: discord.Interaction):
        snapshot = tracemalloc.take_snapshot()
        top_stats = snapshot.statistics("lineno")
        lines = [f"[ Top 10 memory usage ]"]
        for stat in top_stats[:10]:
            lines.append(str(stat))
        # Discord messages have a 2000 character limit
        msg = "\n".join(lines)
        if len(msg) > 1900:
            msg = msg[:1900] + "..."
        await interaction.response.send_message(msg)


async def setup(bot):
    await bot.add_cog(MemoryUsage(bot))
