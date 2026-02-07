from config.weakness_chart import weakness_chart as WEAKNESS_CHART
from utils.loggers.espeon_log import EspeonContext, espeon_log


def get_dex(pokemon_name: str) -> str:
    """Get the Pokédex number for a given Pokémon name."""
    espeon_log("info", f"Fetching Dex number for Pokémon '{pokemon_name}'.")
    pokemon_name = pokemon_name.lower().replace("♀", "-f").replace("♂", "-m")
    if "shiny mega " in pokemon_name:
        pokemon_name = pokemon_name.replace("shiny mega ", "shiny mega-")
    if "mega " in pokemon_name:
        pokemon_name = pokemon_name.replace("mega ", "mega-")
    if "shiny gigantamax " in pokemon_name:
        pokemon_name = pokemon_name.replace("shiny gigantamax ", "shiny gigantamax-")
    if "gigantamax " in pokemon_name:
        pokemon_name = pokemon_name.replace("gigantamax ", "gigantamax-")

    espeon_log("debug", f"Normalized Pokémon name: '{pokemon_name}'.")
    if pokemon_name not in WEAKNESS_CHART:
        espeon_log("info", f"Pokémon '{pokemon_name}' not found in the weakness chart.")
        return "N/A"
    dex_number = WEAKNESS_CHART.get(pokemon_name, {}).get("dex")
    if dex_number is None:
        espeon_log(
            "error", f"Dex number for Pokémon '{pokemon_name}' is not available."
        )
        return None

    # Remove leading zeros, but ensure '0' is returned if dex_number is all zeros
    dex_number = dex_number.lstrip("0") or "0"
    espeon_log("info", f"Found Dex number {dex_number} for Pokémon '{pokemon_name}'.")
    return dex_number
