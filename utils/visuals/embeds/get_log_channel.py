from discord.ext import commands
from config.current_setup import STRAYMONS_GUILD_ID
from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
LOG_CHANNEL_ID = STRAYMONS__TEXT_CHANNELS.server_logs
# Get the guild first
def get_log_channel(bot: commands.Bot):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    return guild.get_channel(LOG_CHANNEL_ID) if guild else None
