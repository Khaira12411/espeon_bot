from config.aesthetic import Espeon_Emoji
from config.straymons_constants import STRAYMONS__ROLES

CHERRY_PIN = "<:cherry_pin:1435953589913915392>"
DIVIDER = "https://media.discordapp.net/attachments/1393740397905313912/1412599078600183829/image.png?ex=690de9a9&is=690c9829&hm=83ee27ffa46657d97c6df2966eb074480a1264e3e5abd854b55517cfa05ccb63&=&format=webp&quality=lossless&width=1812&height=96"
LEADERBOARD_THUMBNAIL = "https://media.discordapp.net/attachments/1394913073520967680/1444680927371329536/26c1c6f85c586cebc7edca90fe1027ea-removebg-preview.png?ex=692d9775&is=692c45f5&hm=775953121ec0b7bba1579428e4234f07d84bdc9301fa168d54e90fb64c9eb741&=&format=webp&quality=lossless"
COLOR = 0xFF90BB
SHOP_EVENT = True

SERVER_CURRENCY_EMOJI = Espeon_Emoji.lumire
SERVER_CURRENCY_NAME = "Lumière Coin"
EVENT_NAME = "Del Le Frume"

SPECIAL_EVENT_ROLE_ID = STRAYMONS__ROLES.valiants

POINT_MAP = {
    "legendary": {"points": 1, "context": "Legendary"},
    "fishing_legendary": {"points": 1, "context": "Fishing Legendary"},
    "fishing_shiny": {"points": 1, "context": "Fishing Shiny"},
    "fishing_exclusive_checklist": {
        "points": 1,
        "context": "Fishing Exclusive Checklist",
    },
    "fishing_shiny_exclusive_checklist": {
        "points": 1,
        "context": "Fishing Shiny Exclusive Checklist",
    },
    "event_shiny": {"points": 1, "context": "Shiny Checklist"},
    "event_exclusive": {"points": 1, "context": "Event Exclusive Checklist"},
    "full_odds_shiny": {"points": 1, "context": "Shiny Full-Odds"},
    "shiny_legendary_full_odds": {"points": 1, "context": "Shiny Legendary Full-Odds"},
}
