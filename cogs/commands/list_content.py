import asyncio
import io
import re

import discord
from discord import app_commands
from discord.ext import commands

# 📁 cogs/commands/owner/list_contents.py


OWNER_ID = 123456789012345678  # 🔒 Replace this with your actual Discord user ID!


# 💜━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🛠️ Owner Command: /list-contents
# Inspects a message and reveals its content + embed info
# 💜━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


class MessageInspectWretch(
    commands.Cog
):  # Wretch = themed for debug/diagnostic cuteness!
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="list-contents",
        description="🔍 Show the content and embed structure of a message! (Owner only)",
    )
    @app_commands.describe(message_link="🔗 The full message link to inspect")
    async def list_contents(self, interaction: discord.Interaction, message_link: str):
        await interaction.response.defer(ephemeral=False)
        await asyncio.sleep(0.5)  # ⏳ Small delay for comfy UX

        # 🧩━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 🔗 Parse the message link to get channel + message ID
        # 🧩━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        match = re.match(
            r"https://(?:canary\.|ptb\.)?discord\.com/channels/\d+/(\d+)/(\d+)",
            message_link,
        )
        if not match:
            return await interaction.followup.send(
                "🚫 Oopsies! That message link doesn't look valid."
            )

        channel_id, message_id = map(int, match.groups())
        channel = interaction.guild.get_channel(channel_id)

        if not channel:
            return await interaction.followup.send(
                "❌ I couldn’t find the channel in this server!"
            )

        try:
            message = await channel.fetch_message(message_id)
        except discord.NotFound:
            return await interaction.followup.send(
                "😢 The message doesn’t seem to exist anymore…"
            )

        # 🧾━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📋 Collecting message content + embed data
        # 🧾━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        parts = []

        # 🔗 Link to message
        msg_link = f"https://discord.com/channels/{interaction.guild.id}/{channel_id}/{message_id}"
        parts.append(f"[🔗 **Link to Original Message**]({msg_link})")

        # 👤 Author info
        parts.append(f"**Author:** {message.author.mention} (`{message.author}`)")

        # 💬 Message content
        if message.content:
            parts.append(f"**Message Content:**\n```text\n{message.content}```")

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
                    embed_parts.append(
                        f"**Field: {field.name}**\n```text\n{field.value}```"
                    )
            parts.append("\n".join(embed_parts))

        if not parts:
            return await interaction.followup.send(
                "🪹 This message has no visible content or embeds to inspect."
            )

        full_text = "\n\n".join(parts)

        # 📤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 📨 Send results (as message or file if too long)
        # 📤━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        if len(full_text) <= 2000:
            await interaction.followup.send(full_text)
        else:
            file = discord.File(
                fp=io.StringIO(full_text), filename="message_contents.txt"
            )
            await interaction.followup.send(
                "📄 The content was too long! Here’s a file instead:", file=file
            )


# ⚙️━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 🔧 Setup function to load the wretch command
# ⚙️━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━


async def setup(bot):
    await bot.add_cog(MessageInspectWretch(bot))
