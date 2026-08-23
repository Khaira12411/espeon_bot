import re
from typing import Dict

import discord

from config.aesthetic import *
from config.wb_constants import *
from utils.cache.cache_list import WB_PING_CACHE

# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━
#   ✨ Espeon Core Function › WB SUB PINGER ✨
# 🤍━━━━━━━━━━━━━━━━━━━━━━━━━━


async def ping_wb_subscribers(bot: discord.Client, message: discord.Message):
    """
    Ping all users subscribed to a world boss based on the message content.
    Handles variants (regular/shiny/both) and sends in the correct channels or DMs.
    Fully defensive with debug logging for cache issues.
    """

    try:
        # Early exit if cache is empty
        if not WB_PING_CACHE:
            return  # no subscribers

        # Include embed text so the spawn embed fields are searchable
        embed_text = ""
        for embed in message.embeds:
            parts = [embed.title or "", embed.description or ""]
            for field in embed.fields:
                parts.append(f"{field.name} {field.value}")
            embed_text += " ".join(parts) + " "

        content = (str(message.content) + " " + embed_text).lower()

        # Only process actual spawn messages, not vote-count warnings
        if "has spawned" not in content:
            return

        # Extract boss_name after 'gigantamax-' or 'eternamax-'
        gmax_match = re.search(r"gigantamax-([a-z0-9\-]+)", content)
        emax_match = re.search(r"eternamax-([a-z0-9\-]+)", content)
        if gmax_match:
            boss_name = gmax_match.group(1).lower()
            form_prefix = "Gigantamax"
        elif emax_match:
            boss_name = emax_match.group(1).lower()
            form_prefix = "Eternamax"
        else:
            return

        # Determine variant
        emoji = WBEmojis.Gmax
        variant = "shiny" if "shiny" in content else "regular"
        if variant == "shiny":
            emoji = WBEmojis.Sgmax

        display_boss_name = f"{emoji} {form_prefix}-{boss_name.title()}"
        pings_by_channel: Dict[int, list[int]] = {}
        dm_user_ids: list[tuple[int, int | None]] = []  # (user_id, channel_id)

        for user_id, bosses in WB_PING_CACHE.items():
            if not isinstance(bosses, dict):
                print(
                    f"[ping_wb_subscribers] Skipping user {user_id}: bosses not a dict"
                )
                continue

            for sub_boss_name_raw, info in bosses.items():
                try:
                    sub_boss_name = str(sub_boss_name_raw).lower()
                    sub_variant = str(info.get("variant", "regular")).lower()
                    channel_id = info.get("channel_id")
                    mode = str(info.get("mode", "channel")).lower()

                    # Boss & variant match
                    if sub_boss_name != boss_name:
                        continue

                    if not (
                        (variant == "shiny" and sub_variant in ("shiny", "both"))
                        or (variant == "regular" and sub_variant in ("regular", "both"))
                    ):
                        continue

                    if mode == "dm":
                        dm_user_ids.append(
                            (
                                user_id,
                                channel_id if isinstance(channel_id, int) else None,
                            )
                        )
                    else:
                        if not isinstance(channel_id, int):
                            print(
                                f"[ping_wb_subscribers] Skipping {user_id} {sub_boss_name}: invalid channel_id"
                            )
                            continue
                        pings_by_channel.setdefault(channel_id, []).append(user_id)

                except Exception as inner_e:
                    print(
                        f"[ping_wb_subscribers] Skipping subscription for user {user_id}, boss '{sub_boss_name_raw}': {inner_e}\nEntry: {info}"
                    )

        # Send channel pings
        for channel_id, user_ids in pings_by_channel.items():
            try:
                mentions = " ".join(f"<@{uid}>" for uid in set(user_ids))
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(
                        f"{Espeon_Emoji.purple_heart_message} {mentions} {display_boss_name} has spawned! Don't forget to register your team ~",
                        allowed_mentions=discord.AllowedMentions(users=True),
                    )
                else:
                    for uid in set(user_ids):
                        try:
                            user = await bot.fetch_user(uid)
                            await user.send(
                                f"{Espeon_Emoji.purple_heart_message} {display_boss_name} has spawned! Don't forget to register your team ~"
                            )
                        except Exception as dm_e:
                            print(f"[ping_wb_subscribers] Failed to DM {uid}: {dm_e}")

            except Exception as send_e:
                print(
                    f"[ping_wb_subscribers] Failed to send in channel {channel_id}: {send_e}"
                )

        # Send DMs for users with mode = "dm"
        for uid, fallback_channel_id in set(dm_user_ids):
            try:
                user = await bot.fetch_user(uid)
                await user.send(
                    f"{Espeon_Emoji.purple_heart_message} {display_boss_name} has spawned! Don't forget to register your team ~"
                )
            except Exception as dm_e:
                print(
                    f"[ping_wb_subscribers] Failed to DM {uid}: {dm_e} — trying channel fallback"
                )
                if fallback_channel_id:
                    try:
                        channel = bot.get_channel(fallback_channel_id)
                        if channel:
                            await channel.send(
                                f"{Espeon_Emoji.purple_heart_message} <@{uid}> {display_boss_name} has spawned! Don't forget to register your team ~",
                                allowed_mentions=discord.AllowedMentions(users=True),
                            )
                        else:
                            print(
                                f"[ping_wb_subscribers] Fallback channel {fallback_channel_id} not found for {uid}"
                            )
                    except Exception as fallback_e:
                        print(
                            f"[ping_wb_subscribers] Fallback channel send failed for {uid}: {fallback_e}"
                        )

    except Exception as e:
        print(f"[ping_wb_subscribers] General failure: {e}")
