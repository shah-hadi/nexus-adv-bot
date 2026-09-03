import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import discord
from discord.ext import commands
from dotenv import load_dotenv

from utils.logger import CommandLogger
from utils.settings import prefixes
from utils.theme import FAILURE_COLOR, emoji

load_dotenv(ROOT / ".env")
TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

intents = discord.Intents.default()
intents.message_content = True
intents.members = True


class Bot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=prefixes, intents=intents, owner_id=OWNER_ID, help_command=None)
        self.command_logger = CommandLogger(self)

    async def setup_hook(self):
        for path in (ROOT / "cogs").glob("*.py"):
            if not path.name.startswith("__"):
                await self.load_extension(f"cogs.{path.stem}")
        await self.tree.sync()

    async def on_command_completion(self, ctx):
        await self.command_logger.log(ctx, "completed")

    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandNotFound):
            return
        if ctx.cog is not None and ctx.cog.has_error_handler():
            return
        detail = error.original if isinstance(error, commands.CommandInvokeError) else error
        detail_text = " ".join(str(detail).split())[:500]
        embed = discord.Embed(
            description=f"{emoji('fail')} The command could not be completed: {detail_text}",
            color=FAILURE_COLOR,
        )
        await ctx.reply(embed=embed, mention_author=False)


if not TOKEN:
    raise RuntimeError("BOT_TOKEN is missing from the environment")

Bot().run(TOKEN)
