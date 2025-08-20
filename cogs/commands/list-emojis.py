import io
import re

import discord
from discord import app_commands
from discord.ext import commands


def to_class_name(name: str) -> str:
    parts = re.findall(r"[A-Za-z0-9]+", name)
    return "".join(part.capitalize() for part in parts) or "GuildEmojis"


class EmojiLister(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="list-emojis", description="Generate emoji class for this server"
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def list_emojis(self, interaction: discord.Interaction):
        guild = interaction.guild
        if not guild:
            await interaction.response.send_message(
                "This command must be used in a server.", ephemeral=True
            )
            return

        class_name = to_class_name(guild.name)

        lines = [f"class {class_name}_Emojis:"]
        if not guild.emojis:
            lines.append("    # No custom emojis found in this server.")
        else:
            for emoji in guild.emojis:
                lines.append(f'    {emoji.name} = "<:{emoji.name}:{emoji.id}>"')

        file_content = "\n".join(lines)
        file = discord.File(fp=io.StringIO(file_content), filename=f"{class_name}.txt")

        await interaction.response.send_message(
            content=f"Here is the emoji class for **{guild.name}**:",
            file=file,
            ephemeral=True,
        )

    list_emojis.extras = {"category": "Owner"}


async def setup(bot: commands.Bot):
    await bot.add_cog(EmojiLister(bot))
