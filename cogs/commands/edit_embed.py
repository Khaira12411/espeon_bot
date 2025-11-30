import discord
from discord import app_commands
from discord.ext import commands
from discord.ui import Modal, TextInput

from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from utils.essentials.loader import pretty_defer
from utils.essentials.role_checks import *
from utils.loggers.espeon_log import EspeonContext, espeon_log


# 🍭──────────────────────────────
#   🎀 Modal: Staff Message Edit
# 🍭──────────────────────────────
class Staff_Message_Edit_Modal(Modal):
    def __init__(
        self,
        bot: commands.Bot,
        user: discord.Member,
        channel: discord.TextChannel,
        message: discord.Message,
    ):
        super().__init__(title="Edit Message Details")
        self.bot = bot
        self.user = user
        self.channel = channel
        self.message = message

        message_content = message.content if message.content else ""
        embed_title = message.embeds[0].title if message.embeds else ""
        embed_description = message.embeds[0].description if message.embeds else ""

        self.content_input = TextInput(
            style=discord.TextStyle.paragraph,
            required=False,
            label="Message Content",
            placeholder="Enter the content of the message to send (Message Outside of Embed)",
            max_length=2000,
            default=message_content,
        )
        self.embed_title_input = TextInput(
            required=False,
            label="Embed Title",
            placeholder="Enter the title of the embed (Optional)",
            max_length=256,
            default=embed_title,
        )
        self.embed_description_input = TextInput(
            style=discord.TextStyle.paragraph,
            required=False,
            label="Embed Description",
            placeholder="Enter the description of the embed (Optional)",
            max_length=4000,
            default=embed_description,
        )
        # Return if there is no input fields
        self.add_item(self.content_input)
        self.add_item(self.embed_title_input)
        self.add_item(self.embed_description_input)

    async def on_submit(self, interaction: discord.Interaction):
        # Return if there is no inputted fields
        if (
            not self.content_input.value.strip()
            and not self.embed_title_input.value.strip()
            and not self.embed_description_input.value.strip()
        ):
            await interaction.response.send_message(
                "❌ You must provide at least one field to edit.", ephemeral=True
            )
            return

        # Defer
        loader = await pretty_defer(
            interaction=interaction,
            content="Editing message...",
            ephemeral=True,
        )

        # Prepare the embed if title or description is provided
        embed = None
        if (
            self.embed_title_input.value.strip()
            or self.embed_description_input.value.strip()
        ):
            embed = discord.Embed(
                title=self.embed_title_input.value.strip() or None,
                description=self.embed_description_input.value.strip() or None,
                color=COLOR,
            )

        try:
            await self.message.edit(
                content=self.content_input.value.strip() or None,
                embed=embed,
            )
            await loader.success(
                content=f"Successfully edited the message in {self.channel.mention}.",
            )
            espeon_log(
                tag="success",
                message=f"✅ Edited message ID {self.message.id} in channel {self.channel.name} ({self.channel.id}) by {self.user.name} ({self.user.id})",
            )
        except Exception as e:
            await loader.error(content=f"Failed to edit the message: {e}")
            espeon_log(
                message=f"❌ Failed to edit message ID {self.message.id} in channel {self.channel.name} ({self.channel.id}): {e}",
                tag="error",
            )


# 🍭──────────────────────────────
#   🎀 Cog: Staff Message Edit
# 🍭──────────────────────────────


class StaffMessageEditCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(
        name="edit-message", description="Edit a bot message in a channel."
    )
    @app_commands.describe(
        channel="The channel containing the message to edit",
        message_id="The ID of the message to edit",
    )
    @clan_staff_only()
    async def edit_message(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        message_id: str,
    ):
        message_id = int(message_id)
        try:
            message = await channel.fetch_message(message_id)
            if message.author.id != self.bot.user.id:
                await interaction.response.send_message(
                    "❌ I can only edit messages that I have sent.", ephemeral=True
                )
                return
            try:
                modal = Staff_Message_Edit_Modal(
                    bot=self.bot,
                    user=interaction.user,
                    channel=channel,
                    message=message,
                )
                await interaction.response.send_modal(modal)
            except Exception as e:
                await interaction.response.send_message(
                    f"❌ Failed to open the edit modal: {e}", ephemeral=True
                )
                espeon_log(
                    message=f"❌ Failed to open edit modal for message ID {message_id} in channel {channel.name} ({channel.id}): {e}",
                    tag="error",
                )
                return
        except Exception as e:
            await interaction.response.send_message(
                f"❌ Failed to fetch message with ID {message_id} in {channel.mention}: {e}",
                ephemeral=True,
            )
            espeon_log(
                message=f"❌ Failed to fetch message ID {message_id} in channel {channel.name} ({channel.id}): {e}",
                tag="error",
            )
            return


# Cog setup function
async def setup(bot: commands.Bot):
    await bot.add_cog(StaffMessageEditCog(bot))
