import re
from typing import Dict

import discord

from config.wb_constants import *
from config.aesthetic import *

async def ping_wb_subscribers(bot: discord.Client, message: discord.Message):
    """
    Ping all users subscribed to a world boss based on the message content.
    Handles variants (regular/shiny/both) and sends in the correct channels or DMs.
    Fully defensive with debug logging for cache issues.
    """
    from utils.cache.wb_sub_cache import WB_PING_CACHE

    try:
        content = str(message.content).lower()

        # Extract boss_name after 'gigantamax-'
        boss_match = re.search(r"gigantamax-([a-z0-9\-]+)", content)
        if boss_match:
            boss_name = boss_match.group(1).lower()
        else:
            # fallback if no GMAX found
            return

        # Determine variant
        emoji = WBEmojis.Gmax
        variant = "shiny" if "shiny" in content else "regular"
        if variant == "shiny":
            emoji = WBEmojis.Sgmax

        display_boss_name = f"{emoji} Gigantamax-{boss_name.title()}"
        pings_by_channel: Dict[int, list[int]] = {}

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
                    if not isinstance(channel_id, int):
                        print(
                            f"[ping_wb_subscribers] Skipping {user_id} {sub_boss_name}: invalid channel_id"
                        )
                        continue

                    # Boss & variant match
                    if sub_boss_name != boss_name:
                        continue

                    if (variant == "shiny" and sub_variant in ("shiny", "both")) or (
                        variant == "regular" and sub_variant in ("regular", "both")
                    ):
                        pings_by_channel.setdefault(channel_id, []).append(user_id)

                except Exception as inner_e:
                    print(
                        f"[ping_wb_subscribers] Skipping subscription for user {user_id}, boss '{sub_boss_name_raw}': {inner_e}\nEntry: {info}"
                    )

        # Send pings
        for channel_id, user_ids in pings_by_channel.items():
            try:
                mentions = " ".join(f"<@{uid}>" for uid in set(user_ids))
                channel = bot.get_channel(channel_id)
                if channel:
                    await channel.send(
                        f"{Espeon_Emoji.purple_heart_message} {mentions} {display_boss_name} has spawned! Don't forget to register your team ~"
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

    except Exception as e:
        print(f"[ping_wb_subscribers] General failure: {e}")
