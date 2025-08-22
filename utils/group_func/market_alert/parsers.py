# ─────────────────────────────────────────────
# Helper: normalize Mega Pokémon name for database/display
# ─────────────────────────────────────────────
from config.weakness_chart import weakness_chart
from utils.loggers.espeon_log import EspeonContext, espeon_log
from utils.visuals.embeds.weakness_embed import FORM_VARIANTS

FORM_BASE_DEX_OFFSET = 7001
from config.form_base_names import FORM_BASE_NAMES


# ─────────────────────────────────────────────
# Helper: Resolve Pokémon Name and Dex
# ─────────────────────────────────────────────
def resolve_pokemon_input(pokemon_input: str):
    """
    Converts any user input (name or dex) into a normalized Pokémon name and Dex number.
    Handles:
    - Numeric Dex input (normal, shiny, golden, special forms)
    - Name input (including shiny/golden prefixes, Mega forms)
    Returns: (display_name, dex_number)
    """
    pokemon_input = pokemon_input.strip().lower()

    # ── Numeric Dex input ──
    if pokemon_input.isdigit():
        dex_int = int(pokemon_input)

        # Check special forms (7001+)
        form_name, form_base_dex, variant_type = parse_form_pokemon(dex_int)
        if form_name:
            return form_name, dex_int

        # Normal golden/shiny logic
        first_digit = pokemon_input[0]
        prefix = ""
        if first_digit == "9" and len(pokemon_input) > 3:
            base_dex = int(pokemon_input[1:])
            prefix = "Golden "
        elif first_digit == "1" and len(pokemon_input) > 3:
            base_dex = int(pokemon_input[1:])
            prefix = "Shiny "
        else:
            base_dex = int(pokemon_input)

        # Lookup in weakness chart
        for name, data in weakness_chart.items():
            chart_dex = int(str(data.get("dex")).lstrip("0"))
            if chart_dex == base_dex:
                display_name = prefix + format_mega_pokemon_name(name)
                return display_name, dex_int

        raise ValueError(f"No Pokémon found with Dex #{dex_int}")

    # ── Name input ──
    else:
        prefix = ""
        if pokemon_input.startswith("shiny "):
            prefix = "Shiny "
            base_name = pokemon_input[6:]
        elif pokemon_input.startswith("golden "):
            prefix = "Golden "
            base_name = pokemon_input[7:]
        else:
            base_name = normalize_mega_input(pokemon_input)

        chart_data = weakness_chart.get(base_name)
        if not chart_data or "dex" not in chart_data:
            raise ValueError(f"No Pokémon found with name {base_name}")

        display_name = prefix + format_mega_pokemon_name(base_name)

        # Calculate Dex with offsets
        if prefix == "Shiny ":
            dex_number = int(chart_data["dex"]) + 1000
        elif prefix == "Golden ":
            dex_number = int(chart_data["dex"]) + 9000
        else:
            dex_number = int(chart_data["dex"])

        return display_name, dex_number


def normalize_mega_input(name: str) -> str:
    """
    Converts user input for Mega Pokémon into chart-friendly format.
    - Converts 'mega venusaur' -> 'mega-venusaur'
    - Converts 'mega mewtwo y' -> 'mega-mewtwo-y'
    - Leaves other names unchanged
    """
    name = name.strip().lower()
    if name.startswith("mega"):
        return name.replace(" ", "-")  # replace all spaces
    return name


def parse_special_mega_input(name: str) -> int:
    """
    Parses input for Pokémon, handling Shiny/Golden prefixes and Mega forms.
    Always returns the integer dex number.
    """
    name = name.strip().lower()
    prefix = None

    # Detect shiny/golden prefix
    for p in ["shiny", "golden"]:
        if name.startswith(p):
            prefix = p
            name = name[len(p) :].strip()
            break

    # Normalize mega forms
    if name.startswith("mega"):
        name = name.replace(" ", "-")

    # Lookup dex number
    dex_number = weakness_chart[name]["dex"]
    dex_number_int = int(dex_number)

    # Apply shiny/golden offset
    if prefix == "shiny":
        final_dex = dex_number_int + 1
    elif prefix == "golden":
        final_dex = dex_number_int + 2
    else:
        final_dex = dex_number_int

    return final_dex


def format_mega_pokemon_name(name: str) -> str:
    """
    If the Pokémon is a Mega form (input or chart name contains 'mega-'),
    replace hyphen with space and title-case it.
    Otherwise, return name as-is.
    """
    if name.lower().startswith("mega-") or name.lower().startswith("mega "):
        return name.replace("-", " ").title()
    return name


def parse_form_pokemon(dex_int: int):
    """Handles special forms (7001+), returns display-friendly Pokémon name and dex."""
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

    # Handle shiny/golden prefixes
    shiny_golden_tag = ""
    if variant_type == "shiny":
        shiny_golden_tag = "Shiny "
    elif variant_type == "golden":
        shiny_golden_tag = "Golden "

    # Convert mega hyphens to spaces for display
    if base_name.lower().startswith("mega-"):
        base_name = base_name.replace("-", " ")

    # Prepend shiny/golden tag if any
    display_name = f"{shiny_golden_tag}{base_name.title()}"

    base_dex = FORM_BASE_DEX_OFFSET + base_index * 3
    return display_name, base_dex, variant_type
