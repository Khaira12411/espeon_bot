from config.straymons_constants import STRAYMONS__TEXT_CHANNELS
# change
class WebhookURLs:
    market_snipe = "https://discord.com/api/webhooks/1444838662851395584/cO-r_7exW-UhkYFi82SRu7gPn16VErqmZKQgCAC5VNX89GLHJf7Q6ClQ9ybLNgEPN_CH"
    clan_event_log = "https://discord.com/api/webhooks/1444841439350755388/qF2LIGCxLFDUBWhXSyQAr3E0jyQIoMVoP3cqOuYZUhi0-EPgjFNJbgOFU96bQnwWKx9n"


WEBHOOK_MAP = {
    STRAYMONS__TEXT_CHANNELS.market_snipe: WebhookURLs.market_snipe,
    STRAYMONS__TEXT_CHANNELS.clan_event_log: WebhookURLs.clan_event_log,
}
