import discord
from discord.ext import commands

from utils.settings import command_allowed, load_config


async def has_full_access(ctx: commands.Context) -> bool:
    if await ctx.bot.is_owner(ctx.author) or ctx.author.id == ctx.guild.owner_id:
        return True
    admin_id = int(load_config().get("admin_role_id", 0))
    return admin_id and any(role.id == admin_id for role in ctx.author.roles)


def configured_role(name: str):
    async def check(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if await has_full_access(ctx) or command_allowed(ctx.author, name):
            return True
        raise commands.MissingPermissions(["configured command role"])
    return commands.check(check)


def admin_access():
    async def check(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if await has_full_access(ctx):
            return True
        raise commands.MissingPermissions(["administrator role"])
    return commands.check(check)


async def member_access_error(ctx, member: discord.Member) -> str | None:
    bot_member = ctx.guild.me or ctx.guild.get_member(ctx.bot.user.id)
    if bot_member and member.top_role >= bot_member.top_role:
        return "I cannot act on that member because their highest role is equal to or above mine."
    if not await has_full_access(ctx) and member.top_role >= ctx.author.top_role:
        return "You cannot act on a member whose highest role is equal to or above yours."
    return None


async def role_access_error(ctx, role: discord.Role) -> str | None:
    bot_member = ctx.guild.me or ctx.guild.get_member(ctx.bot.user.id)
    if role.is_default() or role.managed:
        return "That role cannot be managed by the bot."
    if bot_member and role >= bot_member.top_role:
        return "I cannot manage that role because it is equal to or above my highest role."
    if not await has_full_access(ctx) and role >= ctx.author.top_role:
        return "You cannot manage a role equal to or above your highest role."
    return None
