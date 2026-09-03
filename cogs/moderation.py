if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import datetime
import re

import discord
from discord.ext import commands

from utils.cog import BaseCog
from utils.converters import MemberLookup, UserLookup
from utils.permissions import configured_role, member_access_error
from utils.theme import DANGER, SUCCESS, WARNING


def parse_duration(value: str):
    match = re.fullmatch(r"(\d+)([smhd])", value.lower().strip())
    if not match:
        return None
    amount, unit = match.groups()
    duration = datetime.timedelta(seconds=int(amount) * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit])
    return duration if datetime.timedelta() < duration <= datetime.timedelta(days=28) else None


class Moderation(BaseCog):
    @commands.hybrid_command(description="Remove a member from the server.")
    @configured_role("kick")
    async def kick(self, ctx, member: MemberLookup, *, reason="No reason provided"):
        if error := await member_access_error(ctx, member):
            return await self.reply(ctx, error, DANGER)
        await member.kick(reason=reason)
        await self.reply(ctx, self.with_reason(f"{member.mention} was removed.", reason), SUCCESS)

    @commands.hybrid_command(description="Ban a member or a user ID from the server.")
    @configured_role("ban")
    async def ban(self, ctx, user: UserLookup, *, reason="No reason provided"):
        member = ctx.guild.get_member(user.id)
        if member and (error := await member_access_error(ctx, member)):
            return await self.reply(ctx, error, DANGER)
        await ctx.guild.ban(user, reason=reason)
        await self.reply(ctx, self.with_reason(f"{user.mention} was banned.", reason), SUCCESS)

    @commands.hybrid_command(aliases=["mute", "to"], description="Timeout a member using 30s, 10m, 2h, or 1d.")
    @configured_role("timeout")
    async def timeout(self, ctx, member: MemberLookup, duration: str, *, reason="No reason provided"):
        parsed = parse_duration(duration)
        if not parsed: return await self.reply(ctx, "Use `30s`, `10m`, `2h`, or `1d` (maximum 28 days).", WARNING)
        if error := await member_access_error(ctx, member): return await self.reply(ctx, error, DANGER)
        await member.timeout(parsed, reason=reason)
        await self.reply(ctx, self.with_reason(f"{member.mention} was timed out for {duration}.", reason), WARNING, success=True)

    @commands.hybrid_command(aliases=["unmute", "rto"], description="Remove a member's timeout.")
    @configured_role("untimeout")
    async def untimeout(self, ctx, member: MemberLookup, *, reason="No reason provided"):
        if error := await member_access_error(ctx, member): return await self.reply(ctx, error, DANGER)
        await member.timeout(None, reason=reason)
        await self.reply(ctx, self.with_reason(f"Timeout removed for {member.mention}.", reason), SUCCESS)

    @commands.hybrid_command(description="Unban a user by their Discord user ID.")
    @configured_role("unban")
    async def unban(self, ctx, user_id: int, *, reason="No reason provided"):
        user = await self.bot.fetch_user(user_id)
        await ctx.guild.unban(user, reason=reason)
        ctx.command_log_target = user
        await self.reply(ctx, self.with_reason(f"{user.mention} was unbanned.", reason), SUCCESS)


async def setup(bot):
    await bot.add_cog(Moderation(bot))
