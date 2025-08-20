import discord
from discord import app_commands

from config.current_setup import ACTIVE_GUILD_ID


class CommandGroups:
    def __init__(self, bot: discord.Client):
        self.bot = bot

        # Hardcoded guild IDs here
        self.straymon_guild_id = ACTIVE_GUILD_ID  # replace with your actual ID

        self.straymon_tree = app_commands.CommandTree(bot)
        self.meowsummit_tree = app_commands.CommandTree(bot)

    async def sync_trees(self):
        await self.straymon_tree.sync(guild=discord.Object(id=self.straymon_guild_id))

    def straymon_commands(self, name=None, description=None):
        def decorator(func):
            cmd_name = name or func.__name__
            cmd_desc = description or func.__doc__ or "No description"
            cmd = app_commands.command(name=cmd_name, description=cmd_desc)(func)
            self.straymon_tree.add_command(
                cmd, guild=discord.Object(id=self.straymon_guild_id)
            )
            return cmd

        return decorator
