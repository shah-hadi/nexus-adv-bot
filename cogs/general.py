if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import io
import re
import discord
from discord.ext import commands

from utils.cog import BaseCog
from utils.converters import MemberLookup, UserLookup
from utils.permissions import configured_role
from utils.settings import set_no_prefix
from utils.theme import BRAND, SUCCESS, WARNING


class General(BaseCog):
    async def replied_message(self, ctx):
        reference = getattr(ctx.message, "reference", None)
        if not reference or not reference.message_id: return None
        return reference.resolved if isinstance(reference.resolved, discord.Message) else await ctx.channel.fetch_message(reference.message_id)
    @commands.hybrid_command(aliases=["noprefixuser"], description="Manage no-prefix access.")
    @commands.is_owner()
    async def noprefix(self, ctx, user: UserLookup, action: str = "add"):
        if action.lower() not in {"add", "give", "remove", "delete"}: return await self.reply(ctx, "Use `add` or `remove`.", WARNING)
        enabled = action.lower() in {"add", "give"}; set_no_prefix(user.id, enabled)
        await self.reply(ctx, f"No-prefix access {'granted' if enabled else 'removed'} for {user.mention}.", SUCCESS)

    @commands.hybrid_command(aliases=["av"], description="Show a profile avatar.")
    @configured_role("avatar")
    async def avatar(self, ctx, user: UserLookup | None = None):
        user = user or ctx.author; embed = discord.Embed(title=f"{user.display_name}'s avatar", color=BRAND)
        embed.set_image(url=user.display_avatar.url); await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Show a profile banner.")
    @configured_role("banner")
    async def banner(self, ctx, user: UserLookup | None = None):
        user = await self.bot.fetch_user((user or ctx.author).id)
        if not user.banner:
            return await self.reply(ctx, f"{user.mention} does not have a profile banner.", WARNING)
        embed = discord.Embed(title=f"{user.display_name}'s banner", color=user.accent_color or BRAND)
        embed.set_image(url=user.banner.url)
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="Send an embedded message.")
    @configured_role("say")
    async def say(self, ctx, *, message: str):
        await ctx.reply(embed=discord.Embed(description=message[:4000], color=BRAND), mention_author=False, allowed_mentions=discord.AllowedMentions.none())

    @commands.hybrid_command(description="Show websocket latency.")
    @configured_role("ping")
    async def ping(self, ctx): await self.reply(ctx, f"Websocket latency: `{round(self.bot.latency * 1000)}ms`", BRAND)

    @commands.hybrid_command(aliases=["user"], description="Show member information.")
    async def userinfo(self, ctx, member: MemberLookup | None = None):
        member = member or ctx.author; embed = discord.Embed(title="Member profile", color=BRAND); embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User", value=f"{member.mention}\n`{member.id}`"); embed.add_field(name="Joined", value=discord.utils.format_dt(member.joined_at, "R"))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(aliases=["server"], description="Show server information.")
    @commands.guild_only()
    async def serverinfo(self, ctx):
        guild = ctx.guild; embed = discord.Embed(title=guild.name, color=BRAND)
        if guild.icon: embed.set_thumbnail(url=guild.icon.url)
        embed.add_field(name="Members", value=str(guild.member_count)); embed.add_field(name="Channels", value=str(len(guild.channels)))
        await ctx.reply(embed=embed, mention_author=False)

    @commands.hybrid_command(description="List members with a role.")
    @configured_role("dumprole")
    async def dumprole(self, ctx, role: discord.Role):
        text = " ".join(member.mention for member in role.members) or "No members have this role."
        embed = discord.Embed(title=f"{role.name} members", description=text[:4000], color=BRAND)
        await ctx.reply(embed=embed, mention_author=False, allowed_mentions=discord.AllowedMentions.none())

    @commands.hybrid_command(description="Copy a custom emoji into this server.")
    @commands.guild_only()
    @configured_role("stealemoji")
    async def stealemoji(self, ctx, emoji: discord.PartialEmoji | None = None, *, name: str | None = None):
        if emoji is None:
            message = await self.replied_message(ctx)
            match = re.search(r"<(?P<animated>a?):(?P<name>[A-Za-z0-9_~]+):(?P<id>\d+)>", message.content if message else "")
            if match:
                emoji = discord.PartialEmoji(
                    name=match.group("name"),
                    id=int(match.group("id")),
                    animated=bool(match.group("animated")),
                )
        if not emoji or not emoji.id: return await self.reply(ctx, "Provide a custom emoji or reply to one.", WARNING)
        emoji_name = re.sub(r"[^A-Za-z0-9_]", "", name or emoji.name or "emoji")[:32] or "emoji"
        extension = "gif" if emoji.animated else "png"
        image_url = f"https://cdn.discordapp.com/emojis/{emoji.id}.{extension}?quality=lossless"
        image = await self.bot.http.get_from_cdn(image_url)
        created = await ctx.guild.create_custom_emoji(name=emoji_name, image=image, reason=f"Added by {ctx.author}")
        await self.reply(ctx, f"Added {created} as `{created.name}`.", SUCCESS)

    @commands.hybrid_command(description="Copy a sticker from a replied message.")
    @configured_role("stealsticker")
    async def stealsticker(self, ctx, *, name: str | None = None):
        message = await self.replied_message(ctx)
        if not message or not message.stickers: return await self.reply(ctx, "Reply to a message containing a sticker.", WARNING)
        sticker = await message.stickers[0].fetch(); sticker_name = (name or sticker.name or "sticker")[:30]
        extension = "json" if sticker.format is discord.StickerFormatType.lottie else "png"
        created = await ctx.guild.create_sticker(name=sticker_name, description=sticker.description or "Copied sticker", emoji=sticker.emoji or "✨", file=discord.File(io.BytesIO(await sticker.read()), filename=f"{sticker_name}.{extension}"), reason=f"Added by {ctx.author}")
        await self.reply(ctx, f"Added sticker `{created.name}`.", SUCCESS)


async def setup(bot): await bot.add_cog(General(bot))
