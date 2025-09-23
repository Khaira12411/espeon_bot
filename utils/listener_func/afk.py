import re
import discord
from utils.loggers.espeon_log import espeon_log, EspeonContext
from config.aesthetic import *


async def afk_reply_on_mention(message: discord.Message):
    """
    Checks if any mentioned or replied-to user is AFK.
    - Only triggers for replies if the replier actually pinged the user.
    - Cleans [AFK]/[afk] tags from display_name (any position).
    Replies once per user per message.
    """
    from utils.cache.afk_user_cache import afk_cache_fetch_user

    try:
        if message.author.bot:
            return  # Ignore bot messages

        afk_users_seen = set()
        afk_users_to_reply = []

        # 1️⃣ Check mentions
        for user in message.mentions:
            if user.id in afk_users_seen:
                continue
            afk_row = afk_cache_fetch_user(user.id)
            if afk_row:
                afk_users_seen.add(user.id)
                afk_users_to_reply.append((user, afk_row))

        # 2️⃣ Check replied-to user (only if pinging was enabled)
        if message.reference and message.reference.resolved:
            replied_user = message.reference.resolved.author
            if (
                replied_user.id not in afk_users_seen
                and replied_user in message.mentions  # ✅ require mention enabled
            ):
                afk_row = afk_cache_fetch_user(replied_user.id)
                if afk_row:
                    afk_users_seen.add(replied_user.id)
                    afk_users_to_reply.append((replied_user, afk_row))

        # 3️⃣ Return early if no AFK users found
        if not afk_users_to_reply:
            return

        # 4️⃣ Build a single reply message
        reply_text = ""
        for user, row in afk_users_to_reply:
            reason = row.get("reason") or "No reason provided"
            started_at = row.get("started_at")

            # 🧹 Clean nickname: remove [AFK]/[afk] anywhere in display_name
            clean_name = re.sub(
                r"\[afk\]", "", user.display_name, flags=re.IGNORECASE
            ).strip()

            reply_text += (
                f"{Espeon_Emoji.purple_moon_cat} **{clean_name}** is currently AFK.\n"
                f"{Espeon_Emoji.purple_llama} **Reason:** {reason}\n"
                f"{Espeon_Emoji.purple_clock} **Started at:** <t:{int(started_at)}:R>\n\n"
            )

        # Strip last newline and send reply
        await message.reply(reply_text.strip())

        espeon_log(
            tag="info",
            message=f"AFK reply sent for users {[u.id for u, _ in afk_users_to_reply]} to {message.author.id}",
            label="🌙 AFK REPLY",
            context=EspeonContext.STRAYMONS,
        )

    except Exception as e:
        espeon_log(
            tag="error",
            message=f"Error in afk_reply_on_mention: {e}",
            label="⚠️ AFK ERROR",
            context=EspeonContext.STRAYMONS,
        )
