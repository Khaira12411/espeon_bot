from datetime import datetime

import discord
import pytz

from config.aesthetic import Espeon_Emoji
from config.current_setup import STRAYMONS_GUILD_ID
from config.petal_lace_settings import SERVER_CURRENCY_EMOJI, COLOR, DIVIDER, SERVER_CURRENCY_NAME, SPECIAL_EVENT_ROLE_ID
from config.straymons_constants import (
    STRAYMONS__EMOJIS,
    STRAYMONS__ROLES,
    STRAYMONS__TEXT_CHANNELS,
)
from utils.database.server_currency import reset_all_balances
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.database.server_shop import remove_all_items
from utils.function.event_func import is_event_active_now_manila
from utils.database.event_roles_db import fetch_all_users_w_role, remove_user_w_role
async def scheduled_petal_lace_opening(bot: discord.Client):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to post Petal Lace news.",
            source="Petal Lace Event Post",
        )
        return

    news_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.clueberry)

    charming_hershey_espresso_role = guild.get_role(
        STRAYMONS__ROLES.charming_hershey_espresso
    )
    straymons_role = guild.get_role(STRAYMONS__ROLES.straymon)
    content = f"{straymons_role.mention} Petal Lace Shop in now open! {Espeon_Emoji.pink_flower_two}"
    NEWS_POST_DESC = f"""## __Carnivalesque__ {Espeon_Emoji.sakura_branch}
This month's event will be of a gacha-like approach and we're moving into the French theme. There will be five boxes that can be bought for 20 {SERVER_CURRENCY_NAME}s {SERVER_CURRENCY_EMOJI} which are:

-# • Lavande box
-# • Pivoine box
-# • Mimosa box
-# • Fleur de Lis box
-# • Rose box

You can earn one {SERVER_CURRENCY_NAME} from successfully getting {STRAYMONS__EMOJIS.legendary} Legendary or {STRAYMONS__EMOJIS.shiny} Shiny Pokémon only, be it from `;p` catching or `;f` fishing. Each box has 10 Pokémon in it and there is also a low chance of a {STRAYMONS__EMOJIS.golden11} Golden Pokémon appearing from it. Aside from the boxes, there is also a daily battle that might interest some members.

Each day during the event, you can live battle with Skaia over at <#1469714983477842061> with some set rules:

-# • Can only use a pre-set team before the event started
-# • Teams cannot be changed during the event (but moves can)
-# • Each participant can only battle once each day, which resets on PokéMeow reset day

If there is one winner for the week, the prize will be given to the winner and a new prize will emerge on the start of the new week. There are four prizes in total, one for each week.
-# This is an optional side event, so if the prizes are unclaimed, it will appear in the next major event.

The event starts from <t:1772168400:f> until <t:1774587600:f>. You also need the <@&1311408569945686138> role to participate.
-# Every participant will receive 1M {STRAYMONS__EMOJIS.pokecoin} when event ends."""

    footer_text = f"Only {SERVER_CURRENCY_NAME} earned after this post are counted."

    embed = discord.Embed(
        description=NEWS_POST_DESC,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_footer(text=footer_text, icon_url=guild.icon.url if guild.icon else None)
    await news_channel.send(content=content, embed=embed)

    # Reset all user server balances
    await reset_all_balances(bot)


async def scheduled_petal_lace_event_end(bot: discord.Client):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to post Petal Lace news.",
            source="Petal Lace Event Post",
        )
        return

    news_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.clueberry)

    charming_hershey_espresso_role = guild.get_role(
        STRAYMONS__ROLES.charming_hershey_espresso
    )
    straymons_role = guild.get_role(STRAYMONS__ROLES.straymon)
    content = f"{straymons_role.mention} The Box Event has ended! {Espeon_Emoji.pink_flower_two}"
    title = "🌸 Message from Skaia"
    desc = f"""That concludes the end of the event! I hope everyone had much fun as I did (I wasn't on much). There might be a rerun of Bingo Event around June again but fingers crossed I hope I'll be free and with enough mental energy to conduct it (I definitely won't).

Khy will reveal what entails inside each of the former event boxes were and to those prizes not claimed, will then be moved to June's prize pool along with Colloseum prizes (Poor Shiny Lucario). Thank you again for playing and hope to see you next time!

-# You have until the weekend to clear your coins, once the new week starts (Monday) it will be gone from your inventory."""
    embed = discord.Embed(
        title=title,
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )
    embed.set_footer(
        text="🌸 Wishing everyone a wonderful rest of the year ahead!",
        icon_url=guild.icon.url if guild.icon else None,
    )
    await news_channel.send(content=content, embed=embed)


async def scheduled_petal_lace_shop_clear(
    bot: discord.Client,
):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to post Petal Lace news.",
            source="Petal Lace Event Post",
        )
        return

    news_channel = guild.get_channel(STRAYMONS__TEXT_CHANNELS.clueberry)

    charming_hershey_espresso_role = guild.get_role(
        STRAYMONS__ROLES.charming_hershey_espresso
    )
    straymons_role = guild.get_role(STRAYMONS__ROLES.straymon)
    content = f"{straymons_role.mention} The Shop is now closed! {Espeon_Emoji.pink_flower_two}"
    desc = f"The shop along with any unused {SERVER_CURRENCY_NAME} {SERVER_CURRENCY_EMOJI} have been removed. Thank you so much for your patron!"
    embed = discord.Embed(
        description=desc,
        color=COLOR,
        timestamp=datetime.now(),
    )
    # Send shop closure message
    await news_channel.send(content=content, embed=embed)

    # Reset all user cherry pin balances
    await reset_all_balances(bot)

    # Clear shop
    await remove_all_items(bot)

async def reset_battle_roles(bot: discord.Client):
    guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if not guild:
        espeon_log(
            "error",
            "Straymons guild not found when trying to reset battle roles.",
            source="Reset Battle Roles",
        )
        return


    # Fetch all users with the special event role
    users_with_role = await fetch_all_users_w_role(bot, SPECIAL_EVENT_ROLE_ID)
    if not users_with_role:
        espeon_log(
            "info",
            "No users found with the special event role when trying to reset battle roles.",
            source="Reset Battle Roles",
        )
        return
    # Check if event is active before removing roles
    is_active, _, context = is_event_active_now_manila()
    if not is_active:
        espeon_log(
            "info",
            "Petal Lace event is not active, skipping battle role reset.",
            source="Reset Battle Roles",
        )
        return
    special_event_role = guild.get_role(SPECIAL_EVENT_ROLE_ID)
    if not special_event_role:
        espeon_log(
            "error",
            "Special event role not found when trying to reset battle roles.",
            source="Reset Battle Roles",
        )
        return

    for user in users_with_role:
        user_id = user.get("user_id")
        member = guild.get_member(user_id)
        if member:
            try:
                await member.remove_roles(special_event_role, reason="Resetting battle roles after Petal Lace event.")
                espeon_log(
                    "info",
                    f"Removed special event role from {member} during battle role reset.",
                    source="Reset Battle Roles",
                )
            except Exception as e:
                espeon_log(
                    "error",
                    f"Error removing special event role from {member} during battle role reset: {e}",
                    source="Reset Battle Roles",
                )
        else:
            # Remove stale database entry if member not found
            await remove_user_w_role(bot, SPECIAL_EVENT_ROLE_ID, user_id)
            espeon_log(
                "info",
                f"Removed stale database entry for user ID {user_id} during battle role reset.",
                source="Reset Battle Roles",
            )
    espeon_log(
        "info",
        "Completed battle role reset for all users with the special event role.",
        source="Reset Battle Roles",
    )
