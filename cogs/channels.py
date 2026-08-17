if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import re

import discord
from discord.ext import commands

from utils.cog import BaseCog
from utils.converters import ChannelLookup, MemberLookup, RoleLookup, UserLookup
from utils.permissions import configured_role, member_access_error, role_access_error
from utils.temporary_roles import TemporaryRoleManager
from utils.theme import BRAND, DANGER, SUCCESS, WARNING


def parse_role_duration(value: str) -> int | None:
    match = re.fullmatch(r"(\d+)([smhdw])", value.lower().strip())
    if not match:
        return None
    amount, unit = match.groups()
    seconds = int(amount) * {"s": 1, "m": 60, "h": 3600, "d": 86400, "w": 604800}[unit]
    return seconds if 10 <= seconds <= 2_592_000 else None


class Channels(BaseCog):
    def __init__(self, bot):
        super().__init__(bot)
        self.temporary_roles = TemporaryRoleManager(bot)

    async def cog_load(self):
        self.temporary_roles.start()

    def cog_unload(self):
        self.temporary_roles.stop()

    @commands.hybrid_command(aliases=["clear"], description="Delete recent messages, optionally from one member.")
    @configured_role("purge")
    async def purge(self, ctx, amount: int, member: MemberLookup | None = None):
        if not 1 <= amount <= 100: return await self.reply(ctx, "Choose an amount between 1 and 100.", WARNING)
        if member is None:
            deleted = await ctx.channel.purge(limit=amount + 1)
            removed = max(0, len(deleted) - 1)
            detail = ""
        else:
            matched = 0

            def from_member(message):
                nonlocal matched
                if message.author.id != member.id or matched >= amount:
                    return False
                matched += 1
                return True

            deleted = await ctx.channel.purge(limit=1000, check=from_member)
            removed = len(deleted)
            detail = f" from {member.mention}"
        ctx.command_log_details = {"Messages deleted": removed}
        await self.reply(ctx, f"Removed {removed} message(s){detail}.", SUCCESS)

    @commands.hybrid_command(description="Lock this channel or another text channel.")
    @configured_role("lock")
    async def lock(self, ctx, channel: ChannelLookup | None = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role); overwrite.send_messages = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Locked by {ctx.author}")
        await self.reply(ctx, f"{channel.mention} is now locked.", WARNING, success=True)

    @commands.hybrid_command(description="Unlock this channel or another text channel.")
    @configured_role("unlock")
    async def unlock(self, ctx, channel: ChannelLookup | None = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role); overwrite.send_messages = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unlocked by {ctx.author}")
        await self.reply(ctx, f"{channel.mention} is now unlocked.", SUCCESS)

    @commands.hybrid_command(aliases=["slow"], description="Set channel slowmode.")
    @configured_role("slowmode")
    async def slowmode(self, ctx, seconds: int):
        if not 0 <= seconds <= 21600: return await self.reply(ctx, "Choose a value between 0 and 21,600 seconds.", WARNING)
        await ctx.channel.edit(slowmode_delay=seconds, reason=f"Changed by {ctx.author}")
        await self.reply(ctx, f"Slowmode is now {'off' if seconds == 0 else f'{seconds} second(s)' }.", BRAND)

    @commands.hybrid_command(description="Hide this channel or another text channel.")
    @configured_role("hide")
    async def hide(self, ctx, channel: ChannelLookup | None = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role); overwrite.view_channel = False
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Hidden by {ctx.author}")
        await self.reply(ctx, f"{channel.mention} is now hidden from @everyone.", WARNING, success=True)

    @commands.hybrid_command(description="Unhide this channel or another text channel.")
    @configured_role("unhide")
    async def unhide(self, ctx, channel: ChannelLookup | None = None):
        channel = channel or ctx.channel
        overwrite = channel.overwrites_for(ctx.guild.default_role); overwrite.view_channel = None
        await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite, reason=f"Unhidden by {ctx.author}")
        await self.reply(ctx, f"{channel.mention} is now visible to @everyone.", SUCCESS)

    @commands.hybrid_command(description="Toggle a role on a member.")
    @configured_role("role")
    async def role(self, ctx, member: MemberLookup, role: RoleLookup):
        error = await member_access_error(ctx, member) or await role_access_error(ctx, role)
        if error: return await self.reply(ctx, error, DANGER)
        if role in member.roles:
            await member.remove_roles(role, reason=f"Removed by {ctx.author}")
            ctx.command_log_details = {"Role action": "Removed"}
            return await self.reply(ctx, f"Removed {role.mention} from {member.mention}.", WARNING, success=True)
        await member.add_roles(role, reason=f"Added by {ctx.author}")
        ctx.command_log_details = {"Role action": "Added"}
        await self.reply(ctx, f"Added {role.mention} to {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Assign a role temporarily using 30m, 2h, 7d, or similar.")
    @configured_role("temprole")
    async def temprole(self, ctx, member: MemberLookup, role: RoleLookup, duration: str, *, reason="No reason provided"):
        seconds = parse_role_duration(duration)
        if seconds is None:
            return await self.reply(ctx, "Invalid duration — use `30m`, `2h`, `7d`, or `2w` (maximum 30 days).", WARNING)
        error = await member_access_error(ctx, member) or await role_access_error(ctx, role)
        if error:
            return await self.reply(ctx, error, DANGER)
        tracked = self.temporary_roles.is_tracked(ctx.guild.id, member.id, role.id)
        if role in member.roles and not tracked:
            return await self.reply(ctx, f"{member.mention} already has {role.mention}; no temporary timer was created.", WARNING)
        if role not in member.roles:
            await member.add_roles(role, reason=reason)
        expires_at = await self.temporary_roles.assign(ctx.guild.id, member.id, role.id, seconds)
        ctx.command_log_details = {"Role action": "Temporary", "Expires": f"<t:{expires_at}:R>"}
        action = "Updated" if tracked else "Assigned"
        message = f"{action} {role.mention} for {member.mention} until <t:{expires_at}:R>."
        await self.reply(ctx, self.with_reason(message, reason), SUCCESS)

    @commands.hybrid_command(aliases=["nick"], description="Change a member nickname.")
    @configured_role("nickname")
    async def nickname(self, ctx, member: MemberLookup, *, name: str):
        if error := await member_access_error(ctx, member): return await self.reply(ctx, error, DANGER)
        await member.edit(nick=name, reason=f"Changed by {ctx.author}")
        await self.reply(ctx, f"Nickname updated for {member.mention}.", SUCCESS)


async def setup(bot):
    await bot.add_cog(Channels(bot))
