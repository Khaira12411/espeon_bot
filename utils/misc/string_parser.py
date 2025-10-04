from config.straymons_constants import STRAYMONS__EMOJIS
Shiny_Emoji = STRAYMONS__EMOJIS.shiny
Golden_Emoji = STRAYMONS__EMOJIS.golden11
PREFIX_EMOJI_MAP = {
    "shiny ": Shiny_Emoji,
    "golden ": Golden_Emoji,
}

# 💜────────────────────────────────────────────
#       [🤍 HELPER] Prefix → Emoji Parser
# 💜────────────────────────────────────────────
def parse_prefix(input_str: str) -> str:
    """
    Detects prefixes like 'shiny ' or 'golden ' and replaces them
    with their corresponding emoji prefix.

    Examples:
        "Shiny Cottonee" → "<:shiny:123...> Cottonee"
        "golden Eevee"   → "<:golden11:123...> Eevee"
        "Eevee"          → "Eevee"
    """
    if not isinstance(input_str, str):
        return input_str

    stripped = input_str.strip()
    lower = stripped.lower()

    for prefix, emoji in PREFIX_EMOJI_MAP.items():
        if lower.startswith(prefix):
            # Remove the text prefix (e.g. "shiny ")
            without_prefix = stripped[len(prefix) :].strip()
            return f"{emoji} {without_prefix.title()}"

    # If no recognized prefix, return as-is
    return stripped.title()
