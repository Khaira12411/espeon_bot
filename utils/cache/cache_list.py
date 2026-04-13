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
mr_weakness_user_cache: dict[int, dict[str, str]] = {}
# Structure
# {
#   user_id: {
#       "user_name": str,
#       "display_type": str
#   }
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
#        "emoji_id": str,
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
#       "description": str,
#       "dex": str,
#   },
#   ...
# }

# 💜────────────────────────────────────────────
#      🟣 User Balance Cache with Username
# 💜────────────────────────────────────────────
user_balance_cache: dict[int, dict] = {}
# Structure:
# {
#   user_id: {
#       "user_name": str,
#       "cherry_pin_balance": int,
#   },

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
# 💜────────────────────────────────────────────
#   🟣 Straymons Members Cache
# 💜────────────────────────────────────────────
straymon_member_cache: dict[int, dict] = {}
# Structure:
# user_id -> {
#   "user_name": str,
#   "channel_id": int
# }

# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
#       🌸 Webhook URL Cache 🌸
# 💫━━━━━━━━━━━━━━━━━━━━━━━━━
webhook_url_cache: dict[int, dict] = {}
# Structure:
# {
#   channel_id: {
#       "channel_name": str,
#       "url": str,
#   },
#   ...

market_value_cache: dict[str, dict] = {}

processed_weakness_messages: set[int] = set()
processed_rare_catches = set()
processed_market_feed_message_ids = set()
processed_snipe_ids = set()
not_weakness_chart_user_names = set()

def clear_processed_message_ids():
    PROCESSED_MSG_LIST = [
        processed_weakness_messages,
        processed_rare_catches,
        processed_market_feed_message_ids,
        processed_snipe_ids,
    ]
    for msg_set in PROCESSED_MSG_LIST:
        msg_set.clear()
