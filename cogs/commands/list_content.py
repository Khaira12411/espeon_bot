import asyncio
import io
import re

import discord
from discord import app_commands
from discord.ext import commands

OWNER_ID = 123456789012345678  # 🔒 Replace this with your actual Discord user ID!

# 💜━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛠️ Owner Command: /list-contents
# Extracts message content, embeds, and raw custom emoji IDs
# 💜━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

class MessageInspectWretch(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="list-contents",
        description="🔍 Show the content and embed structure of a message! (Owner only)",
    )
    @app_commands.describe(message_link="🔗 The full message link to inspect")
    async def list_contents(self, interaction: discord.Interaction, message_link: str):
        await interaction.response.defer(ephemeral=False)
        await asyncio.sleep(0.5)

        # 🧩 Parse the message link
        match = re.match(
            r"https://(?:canary\.|ptb\.)?discord\.com/channels/\d+/(\d+)/(\d+)",
            message_link,
        )
        if not match:
            return await interaction.followup.send(
                "🚫 Invalid message link."
            )

        channel_id, message_id = map(int, match.groups())
        channel = interaction.guild.get_channel(channel_id)
        if not channel:
            return await interaction.followup.send(
                "❌ Channel not found in this server!"
            )

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await interaction.followup.send(
                "😢 The message doesn’t exist anymore."
            )

        # 🧾 Helper to extract all raw custom emoji IDs from text
        def extract_emoji_ids(text: str) -> list[str]:
            return re.findall(r"<a?:\w+:(\d+)>", text)

        parts = []

        # 🔗 Link to message
        msg_link = f"https://discord.com/channels/{interaction.guild.id}/{channel_id}/{message_id}"
        parts.append(f"[🔗 **Link to Original Message**]({msg_link})")

        # 👤 Author info
        parts.append(f"**Author:** {message.author.mention} (`{message.author}`)")

        # 💬 Message content
        if message.content:
            emoji_ids = extract_emoji_ids(message.content)
            content_text = message.content
            parts.append(f"**Message Content:**\n```text\n{content_text}```")
            if emoji_ids:
                parts.append(f"**Raw Emoji IDs in Content:** {', '.join(emoji_ids)}")

        # 📦 Embeds
        for i, embed in enumerate(message.embeds, start=1):
            embed_parts = [f"**Embed #{i}:**"]
            if embed.color:
                embed_parts.append(f"**Color:** `#{embed.color.value:06X}`")
            if embed.title:
                embed_parts.append(f"**Title:**\n```text\n{embed.title}```")
            if embed.description:
                embed_parts.append(f"**Description:**\n```text\n{embed.description}```")

            if embed.author and embed.author.name:
                embed_parts.append(f"**Author:**\n```text\n{embed.author.name}```")
            if embed.footer and embed.footer.text:
                embed_parts.append(f"**Footer:**\n```text\n{embed.footer.text}```")
            if embed.fields:
                for field in embed.fields:
                    ids_name = extract_emoji_ids(field.name)
                    ids_value = extract_emoji_ids(field.value)
                    embed_parts.append(f"**Field: {field.name}**\n```text\n{field.value}```")
                    if ids_name:
                        embed_parts.append(f"**Raw Emoji IDs in Field Name:** {', '.join(ids_name)}")
                    if ids_value:
                        embed_parts.append(f"**Raw Emoji IDs in Field Value:** {', '.join(ids_value)}")
            parts.append("\n".join(embed_parts))

        if not parts:
            return await interaction.followup.send(
                "🪹 No visible content or embeds to inspect."
            )

        full_text = "\n\n".join(parts)

        # 📤 Send results (as message or file if too long)
        if len(full_text) <= 2000:
            await interaction.followup.send(full_text)
        else:
            file = discord.File(fp=io.StringIO(full_text), filename="message_contents.txt")
            await interaction.followup.send(
                "📄 The content was too long! Here’s a file instead:", file=file
            )

    list_contents.extras = {"category": "Owner"}
async def setup(bot):
    await bot.add_cog(MessageInspectWretch(bot))
