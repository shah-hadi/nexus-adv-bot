from enum import Enum

import discord

from utils.emojis import ANIMATED_EMOJIS, EMOJIS


# Shared orange visual identity used by command replies, help, and logging.
BRAND_COLOR = 0xFF8C1A
BRAND = discord.Color(BRAND_COLOR)
FAILURE_COLOR = discord.Color.from_rgb(196, 74, 34)


class ReplyTone(Enum):
    SUCCESS = "success"
    WARNING = "warning"
    DANGER = "danger"


SUCCESS = ReplyTone.SUCCESS
WARNING = ReplyTone.WARNING
DANGER = ReplyTone.DANGER


def emoji(name: str) -> str:
    emoji_id = EMOJIS.get(name)
    if emoji_id is None:
        return ""
    prefix = "a" if name in ANIMATED_EMOJIS else ""
    return f"<{prefix}:{name}:{emoji_id}>"


def emoji_url(name: str) -> str | None:
    emoji_id = EMOJIS.get(name)
    if emoji_id is None:
        return None
    extension = "gif" if name in ANIMATED_EMOJIS else "png"
    return f"https://cdn.discordapp.com/emojis/{emoji_id}.{extension}"


def partial_emoji(name: str) -> discord.PartialEmoji | None:
    emoji_id = EMOJIS.get(name)
    if emoji_id is None:
        return None
    return discord.PartialEmoji(
        name=name,
        id=emoji_id,
        animated=name in ANIMATED_EMOJIS,
    )
