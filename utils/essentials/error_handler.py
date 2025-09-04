from utils.essentials.role_checks import *
from utils.loggers.espeon_log import EspeonContext, espeon_log

async def on_app_command_error(
    interaction: discord.Interaction, error: app_commands.AppCommandError
):
    # Handle your custom role-check failures
    if isinstance(
        error,
        (
            ClanStaffCheckFailure,
            VIPCheckFailure,
            ClanMemberCheckFailure,
            OwnerCheckFailure,
            OwnerCoownerCheckFailure,
        ),
    ):
        await interaction.response.send_message(error.args[0], ephemeral=True)
        return

    # Optional: fallback for other errors
    await interaction.response.send_message("❌ Something went wrong.", ephemeral=True)
    espeon_log(
        "error",
        f"Slash command error: {error}",
        context=None,
        include_trace=True,
    )


