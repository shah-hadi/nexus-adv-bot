if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import discord
from discord.ext import commands

from utils.cog import BaseCog
from utils.converters import MemberLookup, UserLookup
from utils.permissions import configured_role, member_access_error
from utils.theme import BRAND, DANGER, SUCCESS, WARNING


class Voice(BaseCog):
    async def _member_action(self, ctx, member):
        if error := await member_access_error(ctx, member):
            await self.reply(ctx, error, DANGER); return False
        if not member.voice:
            await self.reply(ctx, "That member is not connected to a voice channel.", WARNING); return False
        return True

    @commands.hybrid_command(description="Move a member into your current VC.")
    @configured_role("drag")
    async def drag(self, ctx, member: MemberLookup):
        destination = ctx.author.voice.channel if ctx.author.voice else None
        if not isinstance(destination, (discord.VoiceChannel, discord.StageChannel)): return await self.reply(ctx, "You must be in a voice channel.", WARNING)
        if not await self._member_action(ctx, member): return
        await member.move_to(destination, reason=f"Moved by {ctx.author}"); await self.reply(ctx, f"Moved {member.mention} to {destination.mention}.", SUCCESS)

    @commands.hybrid_command(description="Move a member to a selected voice channel.")
    @configured_role("move")
    async def move(self, ctx, member: MemberLookup, destination: discord.VoiceChannel):
        if not await self._member_action(ctx, member): return
        await member.move_to(destination, reason=f"Moved by {ctx.author}"); await self.reply(ctx, f"Moved {member.mention} to {destination.mention}.", SUCCESS)

    @commands.hybrid_command(description="Move everyone between selected voice channels.")
    @configured_role("mvc")
    async def mvc(self, ctx, source: discord.VoiceChannel, destination: discord.VoiceChannel):
        if source.id == destination.id:
            return await self.reply(ctx, "Choose different source and destination channels.", WARNING)
        members = list(source.members)
        if not members:
            return await self.reply(ctx, f"{source.mention} has no members to move.", WARNING)
        for member in members:
            if error := await member_access_error(ctx, member):
                return await self.reply(ctx, f"Bulk move cancelled: {error}", DANGER)
        for member in members:
            await member.move_to(destination, reason=f"Bulk moved by {ctx.author}")
        await self.reply(ctx, f"Moved {len(members)} member(s) to {destination.mention}.", SUCCESS)

    @commands.hybrid_command(aliases=["kh", "wv"], description="Show a member's voice channel.")
    @configured_role("where")
    async def where(self, ctx, member: MemberLookup):
        if not member.voice: return await self.reply(ctx, f"{member.mention} is not in voice.", WARNING)
        await self.reply(ctx, f"{member.mention} is in {member.voice.channel.mention}.", BRAND)

    @commands.hybrid_command(aliases=["dc"], description="Disconnect a member from voice.")
    @configured_role("disconnect")
    async def disconnect(self, ctx, member: MemberLookup):
        if not await self._member_action(ctx, member): return
        await member.move_to(None, reason=f"Disconnected by {ctx.author}"); await self.reply(ctx, f"Disconnected {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Server mute a member.")
    @configured_role("mutevc")
    async def mutevc(self, ctx, member: MemberLookup):
        if not await self._member_action(ctx, member): return
        await member.edit(mute=True, reason=f"Muted by {ctx.author}"); await self.reply(ctx, f"Server-muted {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Remove server mute.")
    @configured_role("unmutevc")
    async def unmutevc(self, ctx, member: MemberLookup):
        if not await self._member_action(ctx, member): return
        await member.edit(mute=False, reason=f"Unmuted by {ctx.author}"); await self.reply(ctx, f"Removed server mute for {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Server deafen a member.")
    @configured_role("deafenvc")
    async def deafenvc(self, ctx, member: MemberLookup):
        if not await self._member_action(ctx, member): return
        await member.edit(deafen=True, reason=f"Deafened by {ctx.author}"); await self.reply(ctx, f"Server-deafened {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Remove server deafen.")
    @configured_role("undeafenvc")
    async def undeafenvc(self, ctx, member: MemberLookup):
        if not await self._member_action(ctx, member): return
        await member.edit(deafen=False, reason=f"Undeafened by {ctx.author}"); await self.reply(ctx, f"Removed server deafen for {member.mention}.", SUCCESS)

    @commands.hybrid_command(description="Set a VC user limit.")
    @configured_role("vclimit")
    async def vclimit(self, ctx, channel: discord.VoiceChannel, number: int):
        if not 0 <= number <= 99: return await self.reply(ctx, "Choose a limit between 0 and 99.", WARNING)
        await channel.edit(user_limit=number, reason=f"Changed by {ctx.author}"); await self.reply(ctx, f"Set {channel.mention} limit to {number or 'unlimited'}.", SUCCESS)

    @commands.hybrid_command(description="Move a selected VC into your current VC.")
    @configured_role("bringall")
    async def bringall(self, ctx, source: discord.VoiceChannel):
        destination = ctx.author.voice.channel if ctx.author.voice else None
        if not isinstance(destination, discord.VoiceChannel): return await self.reply(ctx, "You must be in a voice channel.", WARNING)
        return await self.mvc(ctx, source, destination)

    @commands.hybrid_command(description="Move yourself to a user's voice channel.")
    @configured_role("join")
    async def join(self, ctx, user: MemberLookup):
        if not ctx.author.voice or not user.voice: return await self.reply(ctx, "Both users must be in voice channels.", WARNING)
        await ctx.author.move_to(user.voice.channel, reason=f"Joined {user}"); await self.reply(ctx, f"Moved you to {user.voice.channel.mention}.", SUCCESS)


async def setup(bot): await bot.add_cog(Voice(bot))
