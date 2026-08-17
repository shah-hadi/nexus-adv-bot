import datetime
import re

import discord
from discord.ext import commands

from utils.theme import DANGER, EMOJI, SUCCESS, WARNING


def permission_names(permissions):
    return ", ".join(permission.replace("_", " ").title() for permission in permissions)


class BaseCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    async def reply(self, ctx, text, color, *, success: bool = False):
        if success or color == SUCCESS:
            icon = EMOJI["check"]
        elif color == WARNING:
            icon = EMOJI["warning"]
        elif color == DANGER:
            icon = EMOJI["wrong"]
        else:
            icon = EMOJI["arrow"]

        line = " ".join(str(text).split())
        options = {"mention_author": False}
        if not success and color in {DANGER, WARNING}:
            ctx.command_failed = True
            if ctx.interaction:
                options["ephemeral"] = True
            else:
                options["delete_after"] = 10
        return await ctx.reply(
            embed=discord.Embed(description=f"{icon} {line}", color=color),
            **options,
        )

    @staticmethod
    def with_reason(text, reason):
        return text if reason == "No reason provided" else f"{text} • **Reason:** {reason}"

    @staticmethod
    def usage(ctx):
        signature = ctx.command.signature if ctx.command else ""
        signature = re.sub(r"\[([^\]=]+)=[^\]]*\]", r"[\1]", signature)
        command = ctx.command.qualified_name if ctx.command else "help"
        return f"{ctx.clean_prefix}{command} {signature}".replace("  ", " ").strip()

    async def cog_command_error(self, ctx, error):
        original = error.original if isinstance(error, commands.CommandInvokeError) else error

        if isinstance(error, commands.MissingPermissions):
            text = "You don't have permission to use this command."
        elif isinstance(error, commands.BotMissingPermissions):
            text = f"I need **{permission_names(error.missing_permissions)}** permission."
        elif isinstance(error, commands.NotOwner):
            text = "Only the bot owner can use this command."
        elif isinstance(error, commands.NoPrivateMessage):
            text = "Use this command inside a server."
        elif isinstance(error, commands.MissingRequiredArgument):
            parameter = error.param.name.replace("_", " ").title()
            text = f"{parameter} required — Usage: `{self.usage(ctx)}`"
        elif isinstance(error, (commands.MemberNotFound, commands.UserNotFound)):
            text = "User not found - mention them or use their ID."
        elif isinstance(error, commands.RoleNotFound):
            text = "Role not found - mention the role or check its name."
        elif isinstance(error, commands.ChannelNotFound):
            text = "Channel not found - mention it and try again."
        elif isinstance(error, commands.CommandOnCooldown):
            retry_at = discord.utils.utcnow() + datetime.timedelta(seconds=error.retry_after)
            text = f"Slow down - try again {discord.utils.format_dt(retry_at, 'R')}."
        elif isinstance(error, commands.BadArgument):
            detail = str(error)
            text = detail if detail.startswith("Multiple ") else f"Invalid input — Usage: `{self.usage(ctx)}`"
        elif isinstance(original, discord.Forbidden):
            text = "My role must be above the target's role, and I need the required permission."
        elif isinstance(original, discord.NotFound):
            text = "That user, message, or channel no longer exists."
        elif isinstance(error, commands.CheckFailure):
            text = "You don't have permission to use this command."
        else:
            text = "Something went wrong - try again in a moment."

        await self.reply(ctx, text, DANGER)
