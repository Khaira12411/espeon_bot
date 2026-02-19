import discord

from config.petal_lace_settings import SPECIAL_EVENT_ROLE_ID
from config.straymons_constants import STRAYMONS__ROLES
from utils.database.event_roles_db import remove_user_w_role
from utils.loggers.espeon_log import EspeonContext, espeon_log

# 🍭──────────────────────────────
#   🎀 Event: On Role Remove
# 🍭──────────────────────────────
async def handle_role_remove(
    bot: discord.Client,
    member: discord.Member,
    role: discord.Role,
):
    """Handle role removal events."""
    role_id = role.id
    # ————————————————————————————————
    # 🩵 Straymon Special Event Role Remove
    # ————————————————————————————————
    if role_id == SPECIAL_EVENT_ROLE_ID:
        espeon_log(
            tag="info",
            message=f"Handling special event role removal for {member}.",
        )

        # Update database to reflect that user has lost the special event role
        await remove_user_w_role(
            bot=bot,
            role_id=role.id,
            user_id=member.id,
        )
