import re
from datetime import datetime

import discord
import pytz
from discord.ext import commands

from config.aesthetic import Espeon_Emoji
from config.current_setup import CC_GUILD_ID, STRAYMONS_GUILD_ID
from config.paldea_galar_dict import legendary_mons, rarity_meta
from config.petal_lace_settings import (
    COLOR,
    DIVIDER,
    POINT_MAP,
    SERVER_CURRENCY_EMOJI,
    SHOP_EVENT,
)
from config.straymons_constants import STRAYMONS__ROLES
from utils.cache.cache_list import user_balance_cache
from utils.database.server_currency import (
    get_user_balance,
    update_user_balance,
    upsert_user_balance,
)
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.function.event_func import is_event_active_now_manila
from utils.function.webhook import send_webhook
from utils.loggers.espeon_log import espeon_log

# key = embed_color
SHINY_COLOR = 16751052
LEGENDARY_COLOR = 10487800
EVENT_EXCLUSIVE_COLOR = 15345163
FISHING_COLOR = 8900346
processed_rare_catches = set()
VALID_COLOR = [SHINY_COLOR, EVENT_EXCLUSIVE_COLOR]

LOW_RARITY_COLORS = [
    rarity_meta["rare"]["color"],
    rarity_meta["superrare"]["color"],
    rarity_meta["common"]["color"],
    rarity_meta["uncommon"]["color"],
]

LOW_RARITIES = ["rare", "super rare", "common", "uncommon", "superrare"]
TEST_BOT_LOG_ID = 1220786187401302036
REAL_BOT_LOG_ID = 1076441765059502233
BOT_LOG_ID = TEST_BOT_LOG_ID
FISHING_EXCLUSIVE_MON = [
    "Keldeo-Resolute",
]
SHINY_FISHIN_EXCLUSIVE_MON = [
    "Shiny Keldeo-Resolute",
]
EVENT_EXCLUSIVE_MON = [
    "miraidon",
    "shiny keldeo-resolute",
    "shiny regirock",
    "shiny regice",
    "shiny registeel",
    "shiny deoxys",
]


# ❀─────────────────────────────────────────❀
#      💖  Extract Rarity from Footer
# ❀─────────────────────────────────────────❀
def extract_rarity_from_footer(footer_text: str) -> str:
    # Extract rarity from embed footer
    rarity_match = re.search(r"Rarity:\s*([A-Za-z]+)", footer_text)
    if rarity_match:
        rarity = rarity_match.group(1).strip().lower().replace(" ", "")
        espeon_log(
            "info",
            f"Extracted rarity from footer: {rarity}",
            source="Event Checklist Caught",
        )
        return rarity
    else:
        espeon_log(
            "info",
            f"Could not extract rarity from footer: {footer_text}",
            source="Event Checklist Caught",
        )
        return None


async def add_points_to_user(
    bot: discord.Client,
    user: discord.Member,
    points: int,
    display_pokemon_name: str,
    message: discord.Message,
    catch_type: str,
):
    """Add points to user's balance."""
    user_id = user.id
    user_name = user.name
    current_balance = user_balance_cache.get(user_id)

    # If user not in cache, upsert to database
    if current_balance is None:
        await upsert_user_balance(bot, user_id, user_name, points)
        new_balance = points
        espeon_log(
            "info",
            f"User '{user_name}' not in cache. Upserted with initial points: {points}",
            source="Event Checklist Caught",
        )
    else:
        new_balance = current_balance["cherry_pin_balance"] + points
        await update_user_balance(
            bot=bot,
            user_id=user_id,
            user_name=user_name,
            new_balance=new_balance,
        )
        espeon_log(
            "info",
            f"Added {points} points to user '{user_name}'. New balance: {new_balance}",
            source="Event Checklist Caught",
        )
    # Send confirmation message
    embed = discord.Embed(
        description=(
            f"You have earned {points} {SERVER_CURRENCY_EMOJI} for catching {display_pokemon_name}!\n"
            f"{Espeon_Emoji.pink_star} **Catch Type:** {catch_type}\n"
            f"{Espeon_Emoji.pink_heart_two} **New Balance:** {new_balance} {SERVER_CURRENCY_EMOJI}"
        ),
        color=COLOR,
    )
    embed.set_author(name=user.display_name, icon_url=user.display_avatar.url)
    if message.embeds and message.embeds[0].image:
        embed.set_thumbnail(url=message.embeds[0].image.url)
    embed.set_image(url=DIVIDER)
    await message.channel.send(content=user.mention, embed=embed)


def extract_member_username_from_embed(embed: discord.Embed) -> str | None:
    """
    Extracts the username from the embed author name, e.g. "Congratulations, frayl!" -> "frayl".
    Returns None if not found.
    """
    if embed.author and embed.author.name:
        # Try 'Congratulations, username!' first
        match = re.search(r"Congratulations, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Well done, username!'
        match = re.search(r"Well done, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
        # Fallback: 'Great work, username!'
        match = re.search(r"Great work, ([^!]+)!", embed.author.name)
        if match:
            return match.group(1).strip()
    return None


async def event_checklist_caught(
    bot: discord.Client,
    before_message: discord.Message,
    after_message: discord.Message,
):
    embed = after_message.embeds[0]
    if not embed:
        return

    embed_color = embed.color.value
    embed_description = embed.description or ""

    rarity = None
    guild = after_message.guild

    success, error_msg = is_event_active_now_manila()
    if not success:
        espeon_log(
            "info",
            f"Event is not active. Skipping processing of catch. Reason: {error_msg}",
            source="Event Checklist Caught",
        )
        return

    if after_message.id in processed_rare_catches:
        return  # Already processed this message

    processed_rare_catches.add(after_message.id)

    # Check if its a rare spawn based on color and description
    if embed_color not in LOW_RARITY_COLORS and "You caught" in embed_description:
        # Identify the user who caught the Pokémon
        member = await get_pokemeow_reply_member(before_message)
        if not member:
            # Extract username from embed as fallback
            username = extract_member_username_from_embed(embed)
            if username:
                from utils.cache.straymons_members_cache import (
                    fetch_straymon_member_id_by_name,
                )

                user_id = fetch_straymon_member_id_by_name(username)
                if user_id:
                    member = guild.get_member(user_id) if guild else None
                    if member:
                        espeon_log(
                            "info",
                            f"Identified member from embed author: {member.display_name}",
                            source="Event Checklist Caught",
                        )
                    else:
                        espeon_log(
                            "info",
                            f"Could not find straymon member in guild for user ID: {user_id}",
                            source="Event Checklist Caught",
                        )
                        return
                else:
                    espeon_log(
                        "info",
                        "Could not find user ID from straymons members cache.",
                        source="Event Checklist Caught",
                    )
                    return
            else:
                espeon_log(
                    "info",
                    "Could not identify member from PokéMeow reply or embed author.",
                    source="Event Checklist Caught",
                )
                return

        # TODO Member is only valid if they have the hershey role
        guild = after_message.guild

        hershey_role = guild.get_role(STRAYMONS__ROLES.charming_hershey_espresso)
        straymon_role = guild.get_role(STRAYMONS__ROLES.straymon)
        if hershey_role not in member.roles or straymon_role not in member.roles:
            espeon_log(
                "info",
                f"Member {member.display_name} does not have the required roles. Skipping.",
                source="Event Checklist Caught",
            )
            return

        catch_type = None
        espeon_log(
            "info",
            f"Processing rare catch for member: {member.display_name}",
            source="Event Checklist Caught",
        )

        # Extract Pokémon name
        pokemon_name = ""
        catch_match = re.search(r"You caught a.*?\*\*([^*]+)\*\*", embed_description)
        if catch_match:
            pokemon_name = catch_match.group(1).strip()
            espeon_log(
                "info",
                f"Extracted Pokémon name: {pokemon_name}",
                source="Event Checklist Caught",
            )
        else:
            espeon_log(
                "info",
                f"Could not extract Pokémon name from description: {embed_description}",
                source="Event Checklist Caught",
            )
            return  # Could not extract Pokémon name

        embed_footer = embed.footer.text

        if pokemon_name.lower() in EVENT_EXCLUSIVE_MON:
            catch_type = "event_exclusive"
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() in LOW_RARITIES:

                return  # Not a rare catch
            if rarity.lower() == "super rare":
                rarity = "superrare"
                return  # Not a rare catch

            elif rarity.lower() == "shiny":
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display

            espeon_log(
                "info",
                f"Identified event exclusive catch: {pokemon_name}, Rarity: {rarity}",
                source="Event Checklist Caught",
            )
        elif embed_color == SHINY_COLOR:
            rarity = "shiny"
            pokemon_name_clean = pokemon_name.replace("Shiny ", "").strip()
            catch_type = "event_shiny"  # Default catch type

            if embed_footer:
                footer_lower = embed_footer.lower()
                is_event = "event" in footer_lower
                is_full_odds = "full-odds" in footer_lower
                is_legendary = pokemon_name_clean.lower() in [
                    mon.lower() for mon in legendary_mons
                ]

                if is_event:
                    catch_type = "event_shiny"
                elif is_full_odds:
                    catch_type = "full_odds_shiny"
                    if is_legendary:
                        catch_type = "shiny_legendary_full_odds"

            pokemon_name = pokemon_name_clean
            espeon_log(
                "info",
                f"Identified shiny catch: {pokemon_name}, Catch Type: {catch_type}",
                source="Event Checklist Caught",
            )

        elif embed_color == EVENT_EXCLUSIVE_COLOR:
            catch_type = "event_exclusive"
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() in LOW_RARITIES:
                return  # Not a rare catch
            if rarity.lower() == "super rare":
                rarity = "superrare"
                return  # Not a rare catch

            espeon_log(
                "info",
                f"Identified event exclusive catch: {pokemon_name}, Rarity: {rarity}",
                source="Event Checklist Caught",
            )

        elif embed_color == LEGENDARY_COLOR:
            rarity = "legendary"
            catch_type = "legendary"
            espeon_log(
                "info",
                f"Identified legendary catch: {pokemon_name}",
                source="Event Checklist Caught",
            )

        elif embed_color not in VALID_COLOR and embed_color != FISHING_COLOR:
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "legendary":
                catch_type = "legendary"
                espeon_log(
                    "info",
                    f"Identified legendary catch from footer: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            else:
                espeon_log(
                    "info",
                    f"Catch is neither shiny, event exclusive, nor legendary: {pokemon_name}",
                    source="Event Checklist Caught",
                )
                return  # Not a rare catch

        elif embed_color == FISHING_COLOR:
            espeon_log(
                "info",
                f"Processing fishing catch for Pokémon: {pokemon_name}",
                source="Event Checklist Caught",
            )
            if pokemon_name in FISHING_EXCLUSIVE_MON:
                catch_type = "fishing_exclusive_checklist"
                rarity = "legendary"
                espeon_log(
                    "info",
                    f"Identified fishing exclusive checklist catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif pokemon_name in SHINY_FISHIN_EXCLUSIVE_MON:
                catch_type = "fishing_shiny_exclusive_checklist"
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                espeon_log(
                    "info",
                    f"Identified fishing shiny exclusive checklist catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif "Shiny" in embed_description:
                rarity = "shiny"
                pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display
                catch_type = "fishing_shiny"
                espeon_log(
                    "info",
                    f"Identified fishing shiny catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            elif pokemon_name in legendary_mons:
                catch_type = "fishing_legendary"
                rarity = "legendary"
                espeon_log(
                    "info",
                    f"Identified fishing legendary catch: {pokemon_name}",
                    source="Event Checklist Caught",
                )
            else:
                espeon_log(
                    "info",
                    f"Fishing catch is neither exclusive, shiny, nor legendary: {pokemon_name}",
                    source="Event Checklist Caught",
                )
                return  # Not a rare fishing catch

    points = POINT_MAP.get(catch_type, {}).get("points", 0)
    rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
    pokemon_name = pokemon_name.title()
    context = POINT_MAP.get(catch_type, {}).get("context", "Unknown")
    display_pokemon_name = f"{rarity_emoji} {pokemon_name}"
    source_image_url = embed.image.url if embed.image else None

    # Add points to user balance
    await add_points_to_user(
        bot=bot,
        user=member,
        points=points,
        display_pokemon_name=display_pokemon_name,
        message=after_message,
        catch_type=context,
    )

    # Log to bot-logs channel
    BOT_LOG_ID = REAL_BOT_LOG_ID
    bot_log_guild = bot.get_guild(STRAYMONS_GUILD_ID)
    if bot_log_guild:
        bot_log_channel = bot_log_guild.get_channel(BOT_LOG_ID)
        if bot_log_channel:
            current_balance_info = user_balance_cache.get(member.id)
            current_balance = (
                current_balance_info["cherry_pin_balance"]
                if current_balance_info
                else 0
            )
            desc = (
                # f"{Espeon_Emoji.pink_link} [Jump to Message]({after_message.jump_url})\n"
                f"{Espeon_Emoji.pink_ribbon} **Member:** {member.mention}\n"
                f"{Espeon_Emoji.loveball} **Pokémon:** {display_pokemon_name}\n"
                f"{Espeon_Emoji.pink_star} **Catch Type:** {context}\n"
                f"{Espeon_Emoji.pink_cupcake} **Reward:** {points}{SERVER_CURRENCY_EMOJI}\n"
                f"{Espeon_Emoji.pink_heart_two} **New Balance:** {current_balance}{SERVER_CURRENCY_EMOJI}"
            )
            embed = discord.Embed(
                title=f"{Espeon_Emoji.pink_celebrate} Rare Catch Detected!",
                url=after_message.jump_url,
                description=desc,
                color=embed_color,
            )
            embed.set_author(
                name=member.display_name, icon_url=member.display_avatar.url
            )
            if source_image_url:
                embed.set_thumbnail(url=source_image_url)

            # await bot_log_channel.send(embed=embed)
            try:
                await send_webhook(
                    bot=bot,
                    channel=bot_log_channel,
                    embed=embed,
                )
                espeon_log(
                    "info",
                    f"Logged rare catch to bot log channel for member: {member.display_name}",
                    source="Event Checklist Caught",
                )
            except Exception as e:
                espeon_log(
                    "error",
                    f"Failed to log rare catch to bot log channel: {e}",
                    source="Event Checklist Caught",
                )
