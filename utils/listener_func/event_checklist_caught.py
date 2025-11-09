import re

import discord
from discord.ext import commands

from config.current_setup import CC_GUILD_ID
from config.paldea_galar_dict import rarity_meta
from utils.essentials.pokemon_reply import get_pokemeow_reply_member
from utils.loggers.espeon_log import espeon_log

# key = embed_color
SHINY_COLOR = 16751052
EVENT_EXCLUSIVE_COLOR = 16751052
processed_rare_catches = set()
VALID_COLOR = [SHINY_COLOR, EVENT_EXCLUSIVE_COLOR]


POINT_MAP = {
    "event_shiny": 1,
    "event_exclusive": 3,
    "full_odds_shiny": 5,
}
TEST_BOT_LOG_ID = 1220786187401302036


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

    # Check if its a rare spawn based on color and description
    if embed_color in VALID_COLOR and "You caught" in embed_description:
        # Identify the user who caught the Pokémon
        member = await get_pokemeow_reply_member(before_message)
        if not member:
            return

        # TODO Member is only valid if they have the hershey role

        if after_message.id in processed_rare_catches:
            return  # Already processed this message

        processed_rare_catches.add(after_message.id)

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
        if embed_color == SHINY_COLOR:
            rarity = "shiny"
            pokemon_name = pokemon_name.replace("Shiny ", "")  # Clean for display

            if embed_footer:
                if "event" in embed_footer.lower():
                    catch_type = "event_shiny"
                elif "full-odds" in embed_footer.lower():
                    catch_type = "full_odds_shiny"

        elif embed_color == EVENT_EXCLUSIVE_COLOR:
            catch_type = "event_exclusive"
            rarity = extract_rarity_from_footer(embed_footer)
            if rarity.lower() == "super rare":
                rarity = "superrare"

        points = POINT_MAP.get(catch_type, 0)
        rarity_emoji = rarity_meta.get(rarity, {}).get("emoji", "")
        pokemon_name = pokemon_name.title()

        display_pokemon_name = f"{rarity_emoji} {pokemon_name}"
        source_image_url = embed.image.url if embed.image else None

        # Log the rare catch for debug for now
        # TODO Add points to user balance
        bot_log_guild = bot.get_guild(CC_GUILD_ID)
        if bot_log_guild:
            bot_log_channel = bot_log_guild.get_channel(TEST_BOT_LOG_ID)
            if bot_log_channel:
                desc = (
                    f"[Jump to Message]({after_message.jump_url})\n\n"
                    f"**Member:** {member.mention}\n"
                    f"**Pokémon:** {display_pokemon_name}\n"
                    f"**Catch Type:** {catch_type.replace('_', ' ').title()}\n"
                    f"**Points:** {points}\n"
                )
                embed = discord.Embed(
                    title="🎉 Rare Catch Detected!",
                    description=desc,
                    color=embed_color,
                )
                embed.set_author(
                    name=member.display_name, icon_url=member.display_avatar.url
                )
                if source_image_url:
                    embed.set_thumbnail(url=source_image_url)
                await bot_log_channel.send(embed=embed)
