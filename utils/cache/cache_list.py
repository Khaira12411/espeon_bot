# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 Market Alert Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
import discord


market_alert_cache: list[dict] = []
# Structure
# {
#   "user_id": int,
#   "pokemon": str,
#   "dex_number": int,
#   "max_price": int,
#   "channel_id": int,
#   "role_id": Optional[int],
#   "notify": bool,
# }
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#   🌸 Market Alert Index Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
_market_alert_index: dict[tuple[str, int], dict] = (
    {}
)  # key = (pokemon.lower(), channel_id)
# Structure
# {
#   (pokemon.lower(), channel_id): {
#       "user_id": int,
#       "pokemon": str,
#       "dex_number": int,
#       "max_price": int,
#       "channel_id": int,
#       "role_id": Optional[int],
#       "notify": bool,
#   }

# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#   🌸 Role Cache for Market Alerts 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
_role_cache: dict[tuple[int, int], discord.Role] = {}
# Structure
# {
#   (guild_id, role_id): discord.Role
# }

# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#   🌸 Mr. Weakness User Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
mr_weakness_user_cache = {}  # user_id -> display_type
# Structure
# {
#   user_id: str (display_type)
# }


# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 EV Tracker Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
ev_tracker_cache: dict[int, dict] = {}
# user_id -> {"user_name": str, "pokemon": str, "dex_number": int, "evs": dict, "goals": dict}
# Structure
# {
#   user_id: {
#       "user_name": str,
#       "pokemon": str,
#       "dex_number": int,
#       "evs": {
#           "hp": int,
#           "atk": int,
#           "def": int,
#           "spa": int,
#           "spd": int,
#           "spe": int,
#       },
#       "goals": {
#           "hp": int,
#           "atk": int,
#           "def": int,
#           "spa": int,
#           "spd": int,
#           "spe": int,
#       },
#   }

# 💜────────────────────────────────────────────
#       🟣 WB Ping Cache 🌸
# 💜────────────────────────────────────────────
WB_PING_CACHE: dict[int, dict[str, dict]] = {}
# Structure:
# {
#   user_id: {
#       boss_name: {
#           "user_id": ..,
#           "user_name": ..,
#           "variant": ..,
#           "boss_name": ..,
#           "mode": ..,
#           "channel_id": ..,
#           "created_at": ..
#       },
#       ...
#   },
#   ...
# }

# 💜────────────────────────────────────────────
#       🟣 AFK User Cache 🌸
# 💜────────────────────────────────────────────
AFK_CACHE: dict[int, dict] = {}
# Structure:
# {
#   user_id: {
#       "user_id": ..,
#       "user_name": ..,
#       "reason": ..,
#       "started_at": ..
#   },
#   ...
# }

# 💜────────────────────────────────────────────
#       🟣 Server Shop Cache 🌸
# 💜────────────────────────────────────────────
server_shop_cache: dict[int, dict] = {}
# Structure:
# {
#   item_id: {
#       "item_name": str,
#       "price": int,
#       "stock": int,
#       "image_link": str,
#   },
#   ...
# }

# 💜────────────────────────────────────────────
#      🟣 Catch Contest Event
# 💜────────────────────────────────────────────
catch_contest_event_cache: dict[int, dict] = {}
# Structure:
# {
#   event_id: {
#       "pokemon": str,
#       "catch_goal": int,
#       "ends_on": int,
#   },
#   ...
# }

# 💜────────────────────────────────────────────
#   🟣 Catch Contest Participants Cache
# 💜────────────────────────────────────────────
catch_contest_participants_cache: dict[
    tuple[int, int], dict
] = {}
# Structure:
# {
#   (event_id, user_id): {
#       "event_id": int,
#       "user_id": int,
#       "user_name": str,
#       "pokemon": str,
#       "pokemon_caught": int,
#   },
#   ...
# }