# -------------------- Imports --------------------
import discord

from config.emojis import TYPE_EMOJI
from config.form_base_names import FORM_BASE_NAMES
from config.weakness_chart import weakness_chart
from utils.loggers.espeon_log import EspeonContext, espeon_log

# -------------------- Constants --------------------
type_emojis = {
    "grass": TYPE_EMOJI.grass,
    "fire": TYPE_EMOJI.fire,
    "water": TYPE_EMOJI.water,
    "electric": TYPE_EMOJI.electric,
    "ice": TYPE_EMOJI.ice,
    "fighting": TYPE_EMOJI.fighting,
    "poison": TYPE_EMOJI.poison,
    "ground": TYPE_EMOJI.ground,
    "flying": TYPE_EMOJI.flying,
    "psychic": TYPE_EMOJI.psychic,
    "bug": TYPE_EMOJI.bug,
    "rock": TYPE_EMOJI.rock,
    "ghost": TYPE_EMOJI.ghost,
    "dragon": TYPE_EMOJI.dragon,
    "dark": TYPE_EMOJI.dark,
    "steel": TYPE_EMOJI.steel,
    "fairy": TYPE_EMOJI.fairy,
    "normal": TYPE_EMOJI.normal,
}

TYPE_COLOR = {
    "grass": 6469722,
    "fire": 16555092,
    "water": 5017806,
    "electric": 16045116,
    "ice": 7522494,
    "fighting": 13386860,
    "poison": 11037382,
    "ground": 13988163,
    "flying": 9087190,
    "psychic": 16020082,
    "bug": 7201172,
    "rock": 12628104,
    "ghost": 5401256,
    "dragon": 813760,
    "dark": 6050916,
    "steel": 5933728,
    "fairy": 15502564,
    "normal": 9739428,
}


FORM_BASE_DEX_OFFSET = 7000


# -------------------- Reusable Parsing Functions --------------------
def parse_normal_pokemon(dex_int: int, first_index: str, dex_count: int):
    """Handles regular Pokemon input (1-6999, or weighted 1001/9001 style for shiny/golden)"""

    # If first digit is 7 and dex has 4 digits, use it as-is
    if first_index == "7" and dex_count == 4:
        base_dex = dex_int
        # Lookup exact dex in weakness_chart
        variant_name = next(
            (
                name
                for name, data in weakness_chart.items()
                if int(data["dex"]) == base_dex
            ),
            None,
        )
    else:
        base_dex = (dex_int - 1) % 1000 + 1
        # Lookup using %1000 and exclude 7xxx dex
        variant_name = next(
            (
                name
                for name, data in weakness_chart.items()
                if int(data["dex"]) % 1000 == base_dex
                and not data["dex"].startswith("7")
            ),
            None,
        )

    shiny_golden_tag = ""
    if dex_count == 4:
        if first_index == "1":
            shiny_golden_tag = "Shiny"
        elif first_index == "9":
            shiny_golden_tag = "Golden"

    if not variant_name:
        espeon_log(
            "warn",
            f"Failed to resolve normal Pokemon for dex {dex_int}",
            context=EspeonContext.ESPEON,
        )

    return variant_name, shiny_golden_tag, base_dex


# -------------------- Form Parser --------------------
FORM_BASE_DEX_OFFSET = 7001
FORM_VARIANTS = ["regular", "shiny", "golden"]


def parse_form_pokemon(dex_int: int):
    """Handles special forms (7001+)"""

    if dex_int < FORM_BASE_DEX_OFFSET:

        return None, None, None

    index = dex_int - FORM_BASE_DEX_OFFSET
    base_index = index // 3
    variant_offset = index % 3

    if base_index >= len(FORM_BASE_NAMES):
        espeon_log(
            "warn", f"Form dex {dex_int} is out of range.", context=EspeonContext.ESPEON
        )

        return None, None, None

    base_name = FORM_BASE_NAMES[base_index]
    variant_type = FORM_VARIANTS[variant_offset]

    shiny_golden_tag = ""
    if variant_type == "shiny":
        shiny_golden_tag = "Shiny"
    elif variant_type == "golden":
        shiny_golden_tag = "Golden"

    base_dex = FORM_BASE_DEX_OFFSET + base_index * 3

    return base_name, shiny_golden_tag, base_dex


# -------------------- Resolver --------------------
def get_pokemon_from_input(pokemon_input: str):
    """Main resolver function: handles name, normal dex, and forms"""
    pokemon = pokemon_input.lower().strip()
    shiny_golden_tag = ""

    for prefix, tag in [("shiny ", "Shiny"), ("golden ", "Golden")]:
        if pokemon.startswith(prefix):
            pokemon = pokemon[len(prefix) :].strip()
            shiny_golden_tag = tag
            break

    normalized_name = pokemon.replace(" ", "-")

    # Name lookup
    if normalized_name in weakness_chart:
        dex_val = int(weakness_chart[normalized_name]["dex"])
        return normalized_name, shiny_golden_tag, dex_val

    # Dex input
    if pokemon.isdigit():
        dex_str = str(pokemon)
        first_index = dex_str[0]
        dex_int = int(pokemon)
        dex_count = len(dex_str)

        return parse_normal_pokemon(dex_int, first_index, dex_count)

    espeon_log(
        "error",
        f"Unresolved Pokemon input: '{pokemon_input}'",
        context=EspeonContext.ESPEON,
    )
    return None, None, None


def clean_display_name(variant_name: str, shiny_golden_tag: str | None = None) -> str:
    """
    Format Pokemon display name:
    - Remove dash for Mega forms (Mega-Abomasnow → Mega Abomasnow)
    - Handle special cases like Mega-Charizard-X → Mega Charizard X
    - Keep Shiny/Golden tags intact
    """
    display_name = variant_name.title()

    if "mega-" in variant_name.lower():
        # Replace "Mega-" with "Mega " then strip remaining dashes
        display_name = display_name.replace("Mega-", "Mega ").replace("-", " ")

    # Add Shiny/Golden tag if present
    if shiny_golden_tag:
        display_name = f"{shiny_golden_tag} {display_name}"

    return display_name


# -------------------- Embed Builder --------------------
def build_weakness_embed_from_input(pokemon_input: str) -> discord.Embed | None:
    variant_name, shiny_golden_tag, base_dex = get_pokemon_from_input(pokemon_input)

    if not variant_name:
        return None

    weaknesses = weakness_chart.get(variant_name)
    if not weaknesses:
        espeon_log(
            "warn",
            f"No weaknesses found for {variant_name}",
            context=EspeonContext.ESPEON,
        )
        return None

    types = weaknesses.get("types", [])
    type_emojis_str = "".join(type_emojis.get(t, "") for t in types)

    # 🟢 Clean up title (fix Mega hyphen issue)
    def clean_display_name(raw_name: str, tag: str | None = None) -> str:
        display_name = raw_name.title()
        if "mega-" in raw_name.lower():
            display_name = display_name.replace("Mega-", "Mega ").replace("-", " ")
        if tag:
            display_name = f"{tag} {display_name}"
        return display_name

    display_name = clean_display_name(variant_name, shiny_golden_tag)
    embed_title = f"{display_name} {type_emojis_str}"

    embed_color = TYPE_COLOR.get(types[0], 0x74CEC0) if types else 0x74CEC0

    mult_order = ["4x", "2x", "1x", "1/2x", "1/4x", "0x"]
    description_lines = []
    for mult in mult_order:
        if mult in weaknesses and weaknesses[mult]:
            types_with_emoji = [
                f"{type_emojis.get(t, '')} {t.capitalize()}" for t in weaknesses[mult]
            ]
            description_lines.append(f"**{mult}**: {', '.join(types_with_emoji)}")

    embed = discord.Embed(
        title=embed_title,
        description="\n\n".join(description_lines),
        color=embed_color,
    )
    return embed


# -------------------- Weakness Display Helper --------------------
def format_weakness_description(weaknesses: dict, mode: str = "full") -> str:
    if not weaknesses:
        return "No weakness data available."

    mult_order = {
        "ultra": ["4x"],
        "super": ["4x", "2x"],
        "truncated": ["4x", "2x"],  # alias for clarity
        "full": ["4x", "2x", "1x", "1/2x", "1/4x", "0x"],
    }

    allowed_multipliers = mult_order.get(mode, mult_order["full"])

    description_lines = []
    for mult in allowed_multipliers:
        if mult in weaknesses and weaknesses[mult]:
            types_with_emoji = [
                f"{type_emojis.get(t, '')} {t.capitalize()}" for t in weaknesses[mult]
            ]
            description_lines.append(f"**{mult}**: {', '.join(types_with_emoji)}")

    return (
        "\n\n".join(description_lines)
        if description_lines
        else "No matching weaknesses."
    )


# -------------------- User Weakness Embed --------------------
def build_user_weakness_embed(
    pokemon_input: str,
    user_id: int,
    user_cache: dict[int, str],  # <-- pass the cache here
) -> discord.Embed | None:
    variant_name, shiny_golden_tag, base_dex = get_pokemon_from_input(pokemon_input)
    if not variant_name:
        return None

    weaknesses = weakness_chart.get(variant_name)
    if not weaknesses:
        espeon_log(
            "warn",
            f"No weaknesses found for {variant_name}",
            context=EspeonContext.ESPEON,
        )
        return None

    types = weaknesses.get("types", [])
    type_emojis_str = "".join(type_emojis.get(t, "") for t in types)

    title_name = f"{variant_name.title()}"
    if shiny_golden_tag:
        title_name = f"{shiny_golden_tag} {title_name}"
    embed_title = f"{title_name} {type_emojis_str}"

    embed_color = TYPE_COLOR.get(types[0], 0x74CEC0) if types else 0x74CEC0

    # 🔹 Fetch from passed cache with safe fallback
    raw_display_type = user_cache.get(user_id, "full")
    display_type = (
        raw_display_type if raw_display_type in ("truncated", "full") else "full"
    )

    description = format_weakness_description(weaknesses, mode=display_type)

    embed = discord.Embed(
        title=embed_title,
        description=description,
        color=embed_color,
    )
    return embed
