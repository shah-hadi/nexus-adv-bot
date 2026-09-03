import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"

CONFIGURABLE_COMMANDS = {
    "avatar", "ban", "banner", "bringall", "deafenvc", "disconnect",
    "drag", "dumprole", "hide", "join", "kick", "lock", "move", "mutevc", "mvc",
    "nickname", "ping", "purge", "role", "say", "slowmode", "stealemoji",
    "stealsticker", "temprole", "timeout", "unban", "undeafenvc", "unhide",
    "unlock", "unmutevc", "untimeout", "vclimit", "where",
}


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    temporary = CONFIG_PATH.with_suffix(".tmp")
    with temporary.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)
        file.write("\n")
    temporary.replace(CONFIG_PATH)


def guild_config(guild_id: int | None) -> dict:
    config = load_config()
    if guild_id is None:
        return {"prefix": config.get("default_prefix", config.get("prefix", "!"))}

    saved = config.get("guilds", {}).get(str(guild_id))
    if saved is not None:
        return saved

    return {
        "prefix": config.get("default_prefix", "!"),
        "log_channel_id": 0,
        "admin_role_id": 0,
        "command_role_ids": {},
    }


def update_guild_config(guild_id: int, **changes) -> dict:
    config = load_config()
    guilds = config.setdefault("guilds", {})
    current = dict(guild_config(guild_id))
    current.update(changes)
    guilds[str(guild_id)] = current
    config.setdefault("default_prefix", "!")
    save_config(config)
    return current


def prefixes(bot, message):
    config = load_config()
    guild_id = message.guild.id if message.guild else None
    prefix = guild_config(guild_id).get("prefix", "!")
    if message.author and message.author.id in config.get("no_prefix_user_ids", []):
        return [prefix, ""]
    return prefix


def command_allowed(member, command_name: str) -> bool:
    allowed_ids = guild_config(member.guild.id).get("command_role_ids", {}).get(command_name, [])
    return bool({role.id for role in member.roles}.intersection(allowed_ids))


def set_no_prefix(user_id: int, enabled: bool) -> None:
    config = load_config()
    user_ids = set(config.get("no_prefix_user_ids", []))
    if enabled:
        user_ids.add(user_id)
    else:
        user_ids.discard(user_id)
    config["no_prefix_user_ids"] = sorted(user_ids)
    save_config(config)
