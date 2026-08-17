import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "config.json"


def load_config() -> dict:
    with CONFIG_PATH.open(encoding="utf-8") as file:
        return json.load(file)


def save_config(config: dict) -> None:
    with CONFIG_PATH.open("w", encoding="utf-8") as file:
        json.dump(config, file, indent=2)
        file.write("\n")


def prefixes(bot, message):
    config = load_config()
    prefix = config.get("prefix", "!")
    if message.author and message.author.id in config.get("no_prefix_user_ids", []):
        return [prefix, ""]
    return prefix


def command_allowed(member, command_name: str) -> bool:
    allowed_ids = load_config().get("command_role_ids", {}).get(command_name, [])
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
