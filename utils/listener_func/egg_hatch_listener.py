import re
from datetime import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.current_setup import CC_GUILD_ID, STRAYMONS_GUILD_ID
from config.paldea_galar_dict import rarity_meta
from config.petal_lace_settings import CHERRY_PIN, COLOR, DIVIDER
from config.straymons_constants import STRAYMONS__ROLES, STRAYMONS__TEXT_CHANNELS
from utils.cache.cache_list import server_shop_cache, user_balance_cache
from utils.database.server_currency import get_user_balance
from utils.database.server_shop import fetch_item_by_name, remove_item_by_name
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.function.webhook import send_webhook
from utils.loggers.debug_log import debug_log, enable_debug
from utils.loggers.espeon_log import EspeonContext, espeon_log



RARE_EGG_EXCLUSIVES = [
    "chingling",
    "mimejr",
    "happiny",
    "chatot",
    "munchlax",
    "riolu",
    "audino",
    "zorua",
    "emolga",
    "ferroseed",
    "golett",
    "pawniard",
    "pancham",
    "spritzee",
    "swirlix",
    "noibat",
    "crabrawler",
    "rockruff",
    "type-null",
    "yamper",
    "nickit",
]
SUPER_RARE_EGG_EXCLUSIVE = ["carbink", "mimikyu"]
LEGENDARY_EGG_EXCLUSIVES = ["manaphy", "victini", "phione"]

TEST_BOT_LOG_ID = 1220786187401302036
REAL_BOT_LOG_ID = 1076441765059502233
BOT_LOG_ID = TEST_BOT_LOG_ID
processed_egg_hatches = set()
SERVER_ID = CC_GUILD_ID


#enable_debug(f"{__name__}.egg_hatch_listener_func")


# ❀─────────────────────────────────────────❀
#      💖  Egg Hatch Listener
# ❀─────────────────────────────────────────❀
async def egg_hatch_listener_func(
    bot: discord.Client,
    message: discord.Message,
):
    """
    Listens for egg hatch messages and logs them.
    """

    embed = message.embeds[0] if message.embeds else None
    content = message.content if message.content else None
    if not embed and not content:
        debug_log(f"No embed or content found in message ID {message.id}, skipping.")
        return


    # Color
    embed_color = embed.color.value if embed and embed.color else None
    thumbnail_url = embed.image.url if embed and embed.image else None

    # Extract Pokemon name from message content
    pokemon_name = None
    if content:
        # Pattern: "just hatched a <:447:...> **Riolu**!"
        hatch_match = re.search(r"just hatched a.*?\*\*([^*]+)\*\*", content)
        if hatch_match:
            pokemon_name = hatch_match.group(1).strip()
            espeon_log(
                tag="info",
                message=f"Detected egg hatch of '{pokemon_name}' from message content.",
                label="💖 EGG HATCH LISTENER",
            ),

    if not pokemon_name:
        # Say why it didnt match
        debug_log(
            f"No pokemon_name matched in message content: '{content}' (ID: {message.id}). "
            f"Pattern used: r'just hatched a.*?\\*\\*([^*]+)\\*\\*'. "
            f"Regex result: {'No match' if not 'hatch_match' in locals() or not hatch_match else hatch_match}"
        )
        return

    member = await get_pokemeow_reply_member(message)
    if not member:
        debug_log(
            f"Could not determine member from message ID {message.id} in {message.channel.name}, skipping."
        )
        return

    if message.id in processed_egg_hatches:
        return
    processed_egg_hatches.add(message.id)

    original_name = pokemon_name
    if "shiny" in pokemon_name.lower():
        # Remove "Shiny" prefix/suffix
        pokemon_name = pokemon_name.lower().replace("shiny", "").strip()
        rarity = "shiny"
        debug_log(
            f"Detected shiny egg hatch for '{original_name}', normalized to '{pokemon_name}'.",
        )
    elif pokemon_name.lower() in RARE_EGG_EXCLUSIVES:
        rarity = "rare"
        debug_log(
            f"Detected rare egg hatch for '{pokemon_name}'.",
        )
    elif pokemon_name.lower() in SUPER_RARE_EGG_EXCLUSIVE:
        rarity = "superrare"
        debug_log(
            f"Detected super rare egg hatch for '{pokemon_name}'.",
        )
    elif pokemon_name.lower() in LEGENDARY_EGG_EXCLUSIVES:
        rarity = "legendary"
        debug_log(
            f"Detected legendary egg hatch for '{pokemon_name}'.",
        )
    else:
        debug_log(
            f"'{pokemon_name}' is not classified as a rare egg hatch, skipping.",
        )
        return  # Not a rare egg hatch

    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    display_name = (
        f"{rarity_emoji} {pokemon_name.title()}"
        if rarity_emoji
        else pokemon_name.title()
    )

    if rarity == "shiny":
        espeon_log(
            tag="info",
            message=(
                f"User {member} hatched a shiny '{original_name}' "
                f"for daisyia quest."
            ),
            label="💖 EGG HATCH LISTENER",
        )
        daisyvia_box_item = None
        # Check if daisyia box is still in shop
        daisyvia_box_item = await fetch_item_by_name(bot, "Daisyia Box")
        if not daisyvia_box_item:
            espeon_log(
                tag="info",
                message=(
                    f"Daisyia Box not found in shop after "
                    f"{member}'s shiny '{original_name}' hatch."
                ),
                label="💖 EGG HATCH LISTENER",
            )
            return

        if daisyvia_box_item:
            user_balance_info = user_balance_cache.get(member.id)
            if user_balance_info:
                # Check if user has bought daisyia box
                has_daisyia_box = user_balance_info.get("bought_daisyia_box", "no")
                if has_daisyia_box == "yes":
                    # Remove from shop
                    await remove_item_by_name("Daisyia Box")
                    espeon_log(
                        tag="info",
                        message=(
                            f"Removed 'Daisyia Box' from shop after "
                            f"{member}'s shiny '{original_name}' hatch for daisyia quest"
                        ),
                        label="💖 EGG HATCH LISTENER",
                    )
                    quest_complete_embed = discord.Embed(
                        title="🌸 Daisyia Quest Complete! 🌸",
                        description=(
                            f"Congratulations {member.mention} on hatching a shiny "
                            f"{pokemon_name.title()}! You have completed the Daisyia "
                            f"quest and the Daisyia Box has been removed from the shop."
                            f"{Espeon_Emoji.pink_flower} Please forward this message in <#1359856208961601638> and wait for Skaia to hand your prize."
                        ),
                        color=COLOR,
                        timestamp=datetime.now(),
                    )
                    quest_complete_embed.set_thumbnail(url=thumbnail_url)
                    quest_complete_embed.set_author(
                        name=member.display_name, icon_url=member.display_avatar.url
                    )
                    await message.channel.send(embed=quest_complete_embed)

                    # Log daisyia quest completion
                    quest_complete_log_embed = discord.Embed(
                        title="🌸 Daisyia Quest Completed 🌸",
                        description=(
                            f"[Jump to Message]({message.jump_url})"
                            f"- **User:** {member.mention}\n"
                            f"- **Pokemon:** {display_name}\n"
                        ),
                        color=COLOR,
                        timestamp=datetime.now(),
                    )
                    quest_complete_log_embed.set_author(
                        name=member.display_name, icon_url=member.display_avatar.url
                    )
                    quest_complete_log_embed.set_thumbnail(url=thumbnail_url)
                    quest_complete_log_embed.set_footer(
                        text=f"User ID: {member.id}",
                        icon_url=(
                            member.guild.icon.url
                            if member.guild and member.guild.icon
                            else None
                        ),
                    )
                    cafe_log_channel = member.guild.get_channel(
                        STRAYMONS__TEXT_CHANNELS.cafe_logs
                    )
                    clan_event_log_channel = member.guild.get_channel(
                        STRAYMONS__TEXT_CHANNELS.clan_event_log
                    )
                    if cafe_log_channel:
                        #await cafe_log_channel.send(embed=quest_complete_log_embed)
                        try:
                            await send_webhook(
                                bot,
                                cafe_log_channel,
                                embed=quest_complete_log_embed,
                            )
                        except Exception as e:
                            espeon_log(
                                tag="warn",
                                message=(
                                    f"⚠️ Failed to send daisyia quest completion "
                                    f"log to cafe log channel: {e}"
                                ),
                                exc=e,
                                label="💖 EGG HATCH LISTENER",
                            )
                    if clan_event_log_channel:
                        try:
                            await send_webhook(
                                bot,
                                clan_event_log_channel,
                                embed=quest_complete_log_embed,
                            )
                            """await clan_event_log_channel.send(
                                embed=quest_complete_log_embed
                            )"""
                        except Exception as e:
                            espeon_log(
                                tag="warn",
                                message=(
                                    f"⚠️ Failed to send daisyia quest completion "
                                    f"log to clan event log channel: {e}"
                                ),
                                exc=e,
                                label="💖 EGG HATCH LISTENER",
                            )
                else:
                    espeon_log(
                        tag="info",
                        message=(
                            f"{member} has not purchased Daisyia Box despite "
                            f"hatching a shiny '{original_name}'."
                        ),
                        label="💖 EGG HATCH LISTENER",
                    )
