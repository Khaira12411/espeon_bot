import discord
from discord.ext import commands
from utils.loggers.espeon_log import espeon_log, EspeonContext
import traceback


async def run_command_safe(
    bot,
    interaction: discord.Interaction,
    slash_cmd_name: str,
    command_func,  # the actual command function to call
    *args,
    **kwargs,
):
    """
    Generic wrapper for slash commands with error logging.

    ✅ Uses espeon_log for errors only.
    ✅ Sends ephemeral error message if something goes wrong.
    """
    target = ""
    if "member" in kwargs:
        target = f" for {kwargs['member']}"
    elif args:
        first_arg = args[0]
        if isinstance(first_arg, discord.Member):
            target = f" for {first_arg}"

    try:
        # 🔹 Call the actual command function with all args & kwargs
        await command_func(bot=bot, interaction=interaction, *args, **kwargs)

    except Exception as e:
        tb_str = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        user = interaction.user
        espeon_log(
            "error",
            (
                f"❌ Error in /{slash_cmd_name}{target} by {user.name} "
                f"({user.id}): {e}\nTraceback:\n{tb_str}"
            ),
            context=EspeonContext.ESPEON,
        )
        try:
            await interaction.followup.send(
                "⚠️ Something went wrong. Please contact Khy.",
                ephemeral=True,
            )
        except Exception as send_exc:
            espeon_log(
                "warn",
                f"⚠️ Failed to notify {interaction.user} about error in /{slash_cmd_name}: {send_exc}",
                context=EspeonContext.ESPEON,
            )


async def safe_send_modal(interaction: discord.Interaction, modal: discord.ui.Modal):
    """
    Safely send a modal, falling back to an ephemeral message if it fails.
    """
    try:
        await interaction.response.send_modal(modal)
    except Exception as e:
        espeon_log(
            "error",
            f"Failed to send modal (fallback triggered): {e}",
            context=EspeonContext.ESPEON,
        )
        try:
            await interaction.response.send_message(
                "❌ Unable to open modal. Please try the command again.",
                ephemeral=True,
            )
        except Exception as send_exc:
            espeon_log(
                "warn",
                f"⚠️ Failed to notify {interaction.user} about modal failure: {send_exc}",
                context=EspeonContext.ESPEON,
            )
