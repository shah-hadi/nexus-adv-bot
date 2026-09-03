"""Download the bot artwork and every custom emoji from one Discord server.

Optional `.env` settings:
    EMOJI_GUILD_ID=123456789012345678
    EMOJI_GUILD_NAME=Kyro
    THEME_OUTPUT_ZIP=kyro_assets.zip
"""

import io
import json
import os
import re
import zipfile
from pathlib import Path

import discord
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

TOKEN = os.getenv("BOT_TOKEN")
GUILD_ID = int(os.getenv("EMOJI_GUILD_ID", "0"))
GUILD_NAME = os.getenv("EMOJI_GUILD_NAME", "Kyro").strip()
OUTPUT_ZIP = ROOT / os.getenv("THEME_OUTPUT_ZIP", "kyro_assets.zip")


def safe_name(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("._")
    return cleaned or "unnamed"


def extension(asset, *, animated: bool | None = None) -> str:
    if animated is None:
        animated = asset.is_animated()
    return "gif" if animated else "png"


async def find_guild(client: discord.Client) -> discord.Guild | None:
    if GUILD_ID:
        guild = client.get_guild(GUILD_ID)
        if guild is not None:
            return guild
        try:
            return await client.fetch_guild(GUILD_ID)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    wanted = GUILD_NAME.casefold()
    return discord.utils.find(lambda guild: guild.name.casefold() == wanted, client.guilds)


async def build_archive(client: discord.Client, guild: discord.Guild) -> tuple[bytes, int, list[str]]:
    buffer = io.BytesIO()
    failures: list[str] = []
    manifest = {
        "guild": {"id": guild.id, "name": guild.name},
        "bot": {"id": client.user.id, "name": str(client.user)},
        "emojis": [],
    }

    # Query Discord directly instead of relying on the incomplete gateway cache.
    emojis = await guild.fetch_emojis()

    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        avatar = client.user.display_avatar
        archive.writestr(f"bot/avatar.{extension(avatar)}", await avatar.read())

        full_bot_user = await client.fetch_user(client.user.id)
        if full_bot_user.banner is not None:
            banner = full_bot_user.banner
            archive.writestr(f"bot/banner.{extension(banner)}", await banner.read())

        used_paths: set[str] = set()
        for custom_emoji in emojis:
            suffix = extension(custom_emoji, animated=custom_emoji.animated)
            filename = f"{safe_name(custom_emoji.name)}.{suffix}"
            path = f"emojis/{filename}"
            if path in used_paths:
                path = f"emojis/{safe_name(custom_emoji.name)}_{custom_emoji.id}.{suffix}"
            used_paths.add(path)

            try:
                archive.writestr(path, await custom_emoji.read())
            except (discord.Forbidden, discord.NotFound, discord.HTTPException) as error:
                failures.append(f"{custom_emoji.name} ({custom_emoji.id}): {error}")
                continue

            manifest["emojis"].append(
                {
                    "id": custom_emoji.id,
                    "name": custom_emoji.name,
                    "animated": custom_emoji.animated,
                    "available": custom_emoji.available,
                    "file": path,
                }
            )

        archive.writestr("manifest.json", json.dumps(manifest, indent=2) + "\n")

    return buffer.getvalue(), len(emojis), failures


class ThemeDownloader(discord.Client):
    def __init__(self):
        intents = discord.Intents.none()
        intents.guilds = True
        intents.emojis_and_stickers = True
        super().__init__(intents=intents)
        self.started = False

    async def on_ready(self):
        if self.started:
            return
        self.started = True

        try:
            print(f"Logged in as {self.user}")
            guild = await find_guild(self)
            if guild is None:
                available = ", ".join(f"{item.name} ({item.id})" for item in self.guilds) or "none"
                raise RuntimeError(
                    f"Target server was not found. Servers visible to the bot: {available}"
                )

            archive_bytes, discovered, failures = await build_archive(self, guild)
            OUTPUT_ZIP.parent.mkdir(parents=True, exist_ok=True)
            OUTPUT_ZIP.write_bytes(archive_bytes)

            downloaded = discovered - len(failures)
            print(f"Downloaded {downloaded}/{discovered} emoji(s) from {guild.name} ({guild.id})")
            if failures:
                print("Failed assets:")
                for failure in failures:
                    print(f"  - {failure}")
            print(f"Saved archive to {OUTPUT_ZIP}")
        finally:
            await self.close()


def main() -> None:
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN is missing. Add it to the project's .env file.")
    ThemeDownloader().run(TOKEN, log_handler=None)


if __name__ == "__main__":
    main()
