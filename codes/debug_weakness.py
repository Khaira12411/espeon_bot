# 🟪 parse_pokemon.py
import os
import sys
import traceback

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config.weakness_chart import weakness_chart
from utils.loggers.espeon_log import espeon_log, ServerContext
# 🟣 Constant for form-based dex offset
FORM_BASE_DEX_OFFSET = 7000


# -------------------- Normal Pokemon Parsing --------------------
def parse_normal_pokemon(dex_int: int, first_index: str, dex_count: int):
    """
    🟪 Parse Pokemon using the normal dex system (non-form).
    Handles shiny/golden variants based on dex length & prefix.
    """
    try:
        base_dex = (dex_int - 1) % 1000 + 1

        shiny_golden_tag = ""
        if dex_count == 4:
            if first_index == "1":
                shiny_golden_tag = "Shiny"
            elif first_index == "9":
                shiny_golden_tag = "Golden"

        variant_name = next(
            (
                name
                for name, data in weakness_chart.items()
                if int(data["dex"]) % 1000 == base_dex
                and not data["dex"].startswith("7")
            ),
            None,
        )

        return variant_name, shiny_golden_tag, base_dex
    except Exception:
        espeon_log("error", traceback.format_exc())
        return None, None, None


# -------------------- Form Pokemon Parsing --------------------
def parse_form_pokemon(dex_int: int):
    """
    🟪 Parse Pokemon that use form-based dex values (7000+).
    Includes shiny/golden handling depending on dex offset.
    """
    try:
        full_form_dex = dex_int - (dex_int - FORM_BASE_DEX_OFFSET) % 3
        diff = dex_int - full_form_dex

        shiny_golden_tag = ""
        if diff == 1:
            shiny_golden_tag = "Shiny"
        elif diff == 2:
            shiny_golden_tag = "Golden"

        variant_name = next(
            (
                name
                for name, data in weakness_chart.items()
                if int(data["dex"]) == full_form_dex
            ),
            None,
        )
        if not variant_name:
            return None, None, None

        base_dex = int(weakness_chart[variant_name]["dex"])
        return variant_name, shiny_golden_tag, base_dex
    except Exception:
        espeon_log("error", traceback.format_exc())
        return None, None, None


# -------------------- General Input Parsing --------------------
def get_pokemon_from_input(pokemon_input: str):
    """
    🟪 Entry point: normalize user input (name or dex),
    strip shiny/golden prefixes, and resolve to chart data.
    """
    try:
        pokemon = pokemon_input.lower().strip()
        shiny_golden_tag = ""

        # ✨ Handle shiny/golden prefixes
        for prefix, tag in [("shiny ", "Shiny"), ("golden ", "Golden")]:
            if pokemon.startswith(prefix):
                pokemon = pokemon[len(prefix) :].strip()
                shiny_golden_tag = tag
                break

        normalized_name = pokemon.replace(" ", "-")

        # 🔎 Name lookup
        if normalized_name in weakness_chart:
            dex_val = int(weakness_chart[normalized_name]["dex"])
            if dex_val >= FORM_BASE_DEX_OFFSET:
                return parse_form_pokemon(dex_val)
            return normalized_name, shiny_golden_tag, dex_val

        # 🔢 Dex number lookup
        if pokemon.isdigit():
            dex_str = str(pokemon)
            first_index = dex_str[0]
            dex_int = int(pokemon)
            dex_count = len(dex_str)

            if dex_count == 4 and first_index == "7":
                return parse_form_pokemon(dex_int)
            else:
                return parse_normal_pokemon(dex_int, first_index, dex_count)

        return None, None, None
    except Exception:
        espeon_log("error", traceback.format_exc())
        return None, None, None
