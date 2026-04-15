from config.new_abilities import abilities as abilities_dict
from config.new_pokemons import pokemons

immunity_abilities = {
    "dry-skin": ["fire"],
    "earth-eater": ["ground"],
    "flash-fire": ["fire"],
    "levitate": ["ground"],
    "lightning-rod": ["electric"],
    "motor-drive": ["electric"],
    "sap-sipper": ["grass"],
    "storm-drain": ["water"],
    "thick-fat": ["fire", "ice"],  # Only half damage from both
    "volt-absorb": [
        "electric"
    ],  # restores hp by 25%  when hit by electric move, but still immune to it
    "water-absorb": [
        "water"
    ],  # restores hp by 25% when hit by water move, but still immune to it
    "well-baked-body": [
        "fire"
    ],  # Immune to fire , raises defenses by 2 stages when hit by fire move
    "wonder-guard": [
        "normal",
    ],  # Shedinja's Wonder Guard only allows super effective moves to hit it, making it immune to all non super effective types
}

# Map for custom immunity descriptions (honoring the comments in immunity_abilities)
immunity_ability_custom_desc = {
    "thick-fat": "Only half damage from Fire and Ice moves.",
    "volt-absorb": "Restores HP by 25% when hit by an Electric move, but still immune to it.",
    "water-absorb": "Restores HP by 25% when hit by a Water move, but still immune to it.",
    "well-baked-body": "Immune to Fire; raises defenses by 2 stages when hit by a Fire move.",
    "wonder-guard": "Shedinja's Wonder Guard only allows super effective moves to hit it, making it immune to all non super effective types.",
}
abilities_to_watch_out_for = {
    # Prevent stat drops
    "Clear Body": "Prevents stat reduction caused by other Pokémon’s moves or abilities.",
    "White Smoke": "Prevents stat reduction caused by other Pokémon’s moves or abilities.",
    "Full Metal Body": "Prevents stat reduction caused by other Pokémon’s moves or abilities.",
    "Hyper Cutter": "Prevents Attack stat reduction.",
    "Keen Eye": "Prevents Accuracy stat reduction.",
    "Big Pecks": "Prevents Defense stat reduction.",
    "Flower Veil": "Prevents stat drops to Grass-type allies.",
    "Mirror Armor": "Reflects stat-lowering effects back to the user.",
    # Punish debuffs
    "Competitive": "Raises Sp. Atk sharply when any stat is lowered.",
    "Defiant": "Raises Attack sharply when any stat is lowered.",
    "Contrary": "Inverts stat changes (so debuffs become buffs, and buffs become debuffs).",
    # Status power-up
    "Guts": "Increases Attack by 50% when the Pokémon has a major status condition (burn, paralysis, poison, sleep, freeze).",
    "Quick Feet": "Increases Speed when statused (ignores Speed drop from paralysis).",
    "Marvel Scale": "Increases Defense by 50% when statused.",
    "Flare Boost": "Increases Special Attack by 50% when burned.",
    "Toxic Boost": "Increases Attack by 50% when poisoned.",
    "Poison Heal": "When poisoned, the Pokémon heals HP instead of taking damage each turn.",
}


def get_ability_effect(ability_name):
    """
    Return the effect description for the given ability name from the abilities dict.
    ability_name: str - The name of the ability (case-insensitive).
    abilities_dict: dict - The abilities dictionary (like your sample above).
    """
    ability = abilities_dict.get(ability_name.lower())
    if ability:
        return ability.get("effect")
    return None


def get_immunities_based_on_abilities(pokemon_name):
    """
    Return a list of types that the given Pokémon is immune to based on its abilities.
    Uses custom descriptions when available, otherwise falls back to generic immunity phrasing.
    Hidden abilities are marked explicitly.
    Special cases:
      - Thick Fat halves damage instead of granting immunity.
      - Wonder Guard: only super effective moves can hit.
    """
    from utils.visuals.embeds.weakness_embed import type_emojis

    immunities = set()
    ability_effects = {}
    notes = []
    abilities = get_pokemon_abilities(pokemon_name)
    if not abilities:
        return [], {}, None

    standard = abilities.get("standard", [])
    hidden = abilities.get("hidden", [])
    all_abilities = standard + hidden
    multiple = len(all_abilities) > 1

    for ability in all_abilities:
        if ability in immunity_abilities:
            types = immunity_abilities[ability]
            immunities.update(types)
            effect = immunity_ability_custom_desc.get(ability)
            if effect:
                clean_effect = effect.replace(", but still immune to it.", "").strip()
                ability_effects[ability] = clean_effect
            else:
                ability_effects[ability] = None
        watch_effect = abilities_to_watch_out_for.get(ability)
        if not watch_effect:
            watch_effect = abilities_to_watch_out_for.get(
                ability.replace("-", " ").title()
            )
        if watch_effect:
            effect = watch_effect
            ability_effects[ability] = effect

    if not ability_effects:
        note = None
    else:
        note_lines = []
        for ability, desc in ability_effects.items():
            ability_name = ability.replace("-", " ").title()
            ability_label = f"**__{ability_name} Ability__**"

            if ability not in immunity_abilities:
                # Keep watch-out descriptions exactly as-is.
                if multiple:
                    if ability in hidden:
                        note_lines.append(
                            f"- If {ability_label} (Hidden Ability) is active: {desc}"
                        )
                    else:
                        note_lines.append(f"- If {ability_label} is active: {desc}")
                else:
                    note_lines.append(f"- {ability_label}: {desc}")

                continue

            types = immunity_abilities[ability]
            formatted_types = [
                f"{type_emojis.get(t, '')} {t.title()}".strip() for t in types
            ]
            type_str = (
                " and ".join(formatted_types)
                if len(formatted_types) > 1
                else formatted_types[0]
            )

            if ability == "thick-fat":
                # Special case: Thick Fat halves damage
                if multiple:
                    if ability in hidden:
                        note_lines.append(
                            f"- If {ability_label} (Hidden Ability) is active, {pokemon_name.title()} takes only half damage from {type_str} moves."
                        )
                    else:
                        note_lines.append(
                            f"- If {ability_label} is active, {pokemon_name.title()} takes only half damage from {type_str} moves."
                        )
                else:
                    note_lines.append(
                        f"- {pokemon_name.title()} takes only half damage from {type_str} moves."
                    )

            elif ability == "wonder-guard":
                # Special case: Wonder Guard
                if multiple:
                    if ability in hidden:
                        note_lines.append(
                            f"- If {ability_label} (Hidden Ability) is active, only super effective moves can hit {pokemon_name.title()}."
                        )
                    else:
                        note_lines.append(
                            f"- If {ability_label} is active, only super effective moves can hit {pokemon_name.title()}."
                        )
                else:
                    note_lines.append(
                        f"- Only super effective moves can hit {pokemon_name.title()}, thanks to Wonder Guard."
                    )

            else:
                # Normal immunity phrasing
                if multiple:
                    if ability in hidden:
                        if desc:
                            note_lines.append(
                                f"- If {ability_label} (Hidden Ability) is active, {pokemon_name.title()} is immune to {type_str}, and {desc}"
                            )
                        else:
                            note_lines.append(
                                f"- If {ability_label} (Hidden Ability) is active, {pokemon_name.title()} is immune to {type_str}."
                            )
                    else:
                        if desc:
                            note_lines.append(
                                f"- If {ability_label} is active, {pokemon_name.title()} is immune to {type_str}, and {desc}"
                            )
                        else:
                            note_lines.append(
                                f"- If {ability_label} is active, {pokemon_name.title()} is immune to {type_str}."
                            )
                else:
                    if desc:
                        note_lines.append(
                            f"- If {ability_label} is active, {pokemon_name.title()} is immune to {type_str}, and {desc}"
                        )
                    else:
                        note_lines.append(
                            f"- If {ability_label} is active, {pokemon_name.title()} is immune to {type_str}."
                        )
        note = "\n".join(note_lines)

    return list(immunities), ability_effects, note


def normalize_pokemon_name(name):
    """
    Convert user input like 'mega-absol' or 'gigantamax-alcremie' to PokéAPI key.
    Handles Mega, Gigantamax, Primal, and regional forms.
    Also strips 'golden' or 'shiny' prefix if present.

    Special note: For Shedinja's Wonder Guard, only fire, flying, rock, ghost, and dark can hit it.
    """
    name = name.lower().replace(" ", "-")
    # Remove golden or shiny prefix
    if name.startswith("golden-"):
        name = name[7:]
    elif name.startswith("shiny-"):
        name = name[6:]
    # Mega forms
    if name.startswith("mega-"):
        base = name[5:]
        # Handle possible -x or -y
        if base.endswith("-x") or base.endswith("-y"):
            return f"{base[:-2]}-mega-{base[-1]}"
        return f"{base}-mega"
    # Gigantamax forms
    if name.startswith("gigantamax-"):
        base = name[11:]
        return f"{base}-gmax"
    # Primal forms
    if name.startswith("primal-"):
        base = name[7:]
        return f"{base}-primal"
    # Alolan, Galarian, Hisuian, Paldean, etc.
    for region in ["alolan", "galarian", "hisuian", "paldean"]:
        if name.startswith(f"{region}-"):
            base = name[len(region) + 1 :]
            return f"{base}-{region}"
    return name


def get_pokemon_stats(name):
    """Return the stats dictionary for the given Pokémon name."""
    key = normalize_pokemon_name(name)
    return pokemons.get(key, {}).get("stats")


def get_pokemon_abilities(name):
    """Return the abilities dictionary for the given Pokémon name."""
    key = normalize_pokemon_name(name)
    return pokemons.get(key, {}).get("abilities")


def format_pokemon_abilities(name) -> str | None:
    """
    Return a formatted ability string for the given Pokémon name.

    Examples:
      Single  -> 'Ability: Levitate'
            Multiple -> 'Abilities: Levitate | Chlorophyll'
    """
    abilities = get_pokemon_abilities(name)
    if not abilities:
        return None

    all_abilities = abilities.get("standard", []) + abilities.get("hidden", [])
    if not all_abilities:
        return None

    formatted = [a.replace("-", " ").title() for a in all_abilities]

    if len(formatted) == 1:
        return f"Ability: {formatted[0]}"
    return f"Abilities: {' | '.join(formatted)}"


def get_pokemons_with_ability(ability_name):
    """Return a list of Pokémon names that have the given ability (standard or hidden)."""
    result = []
    for name, data in pokemons.items():
        abilities = data.get("abilities", {})
        if ability_name in abilities.get(
            "standard", []
        ) or ability_name in abilities.get("hidden", []):
            result.append(name)
    return result


def get_pokemons_by_weight(min_weight=None, max_weight=None):
    """Return a list of Pokémon names filtered by weight (in kg)."""
    result = []
    for name, data in pokemons.items():
        weight = data.get("stats", {}).get("weight")
        if weight is not None:
            if (min_weight is None or weight >= min_weight) and (
                max_weight is None or weight <= max_weight
            ):
                result.append(name)
    return result


def get_pokemons_by_stat(stat, min_value=None, max_value=None):
    """Return a list of Pokémon names filtered by a specific stat."""
    result = []
    for name, data in pokemons.items():
        value = data.get("stats", {}).get(stat)
        if value is not None:
            if (min_value is None or value >= min_value) and (
                max_value is None or value <= max_value
            ):
                result.append(name)
    return result


def pretty_print_pokemon(name):
    """Prints a formatted summary of the Pokémon's stats and abilities."""
    key = normalize_pokemon_name(name)
    data = pokemons.get(key)
    if not data:
        print(f"No data for {name}")
        return
    print(f"{name.title()}\nStats: {data['stats']}\nAbilities: {data['abilities']}")
