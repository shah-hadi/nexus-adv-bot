import datetime

import discord

from utils.settings import guild_config
from utils.theme import BRAND_COLOR, emoji, emoji_url


# One command -> one real icon from the actual asset pack. Anything not
# listed here falls back to "star" instead of raising a KeyError.
COMMAND_ICONS = {
    "kick": "kick",
    "ban": "ban",
    "unban": "unban",
    "timeout": "timeout",
    "untimeout": "untimeout",
    "clear": "clear",
    "lock": "lock",
    "unlock": "unlock",
    "hide": "hide",
    "unhide": "unhide",
    "slowmode": "slowmode",
    "role": "role_add",
    "nickname": "nickname",
    "drag": "drag",
    "move": "move",
    "mvc": "mvc",
    "bringall": "bringall",
    "join": "join",
    "disconnect": "disconnect",
    "mutevc": "mutevc",
    "unmutevc": "unmutevc",
    "deafenvc": "deafenvc",
    "undeafenvc": "undeafenvc",
    "vclimit": "vclimit",
    "where": "where",
    "avatar": "avatar",
    "banner": "banner",
    "say": "reply",
    "ping": "ping",
    "userinfo": "info",
    "serverinfo": "info",
    "stealemoji": "emoji",
    "stealsticker": "sticker",
    "dumprole": "folder",
    "noprefix": "crown",
    "config": "settings",
}


class CommandLogger:
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _arguments(ctx) -> dict:
        arguments = dict(getattr(ctx, "kwargs", {}) or {})
        parameters = list(getattr(ctx.command, "clean_params", {}).values())
        positional_names = [
            parameter.name
            for parameter in parameters
            if parameter.kind.name not in {"KEYWORD_ONLY", "VAR_KEYWORD"}
        ]
        values = list(getattr(ctx, "args", []) or [])
        if positional_names and len(values) >= len(positional_names):
            arguments = dict(zip(positional_names, values[-len(positional_names):])) | arguments
        return arguments

    async def _target(self, ctx, arguments: dict):
        explicit_target = getattr(ctx, "command_log_target", None)
        if isinstance(explicit_target, (discord.Member, discord.User)):
            return explicit_target, explicit_target.mention, explicit_target.display_avatar.url
        if isinstance(explicit_target, discord.Role):
            return explicit_target, explicit_target.mention, None

        for key in ("member", "user"):
            value = arguments.get(key)
            if isinstance(value, (discord.Member, discord.User)):
                return value, value.mention, value.display_avatar.url

        # Some moderation commands accept a raw ID instead of a converter.
        # Resolve those IDs here so their logs still identify the affected user.
        for key in ("user_id", "member_id"):
            value = arguments.get(key)
            if isinstance(value, int):
                user = self.bot.get_user(value)
                if user is None:
                    try:
                        user = await self.bot.fetch_user(value)
                    except (discord.NotFound, discord.HTTPException):
                        user = None
                if user is not None:
                    return user, user.mention, user.display_avatar.url

        role = arguments.get("role")
        if isinstance(role, discord.Role):
            return role, role.mention, None
        return None, None, None

    @staticmethod
    def _icon(command_name: str) -> str:
        root_name = command_name.split()[0]
        return emoji(COMMAND_ICONS.get(command_name, COMMAND_ICONS.get(root_name, "star")))

    async def _get_log_channel(self, ctx) -> discord.TextChannel | None:
        channel_id = int(guild_config(ctx.guild.id).get("log_channel_id", 0))
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        return channel if isinstance(channel, discord.TextChannel) else None

    async def log_config_change(
        self,
        guild: discord.Guild,
        actor: discord.Member | discord.User,
        action: str,
        details: dict,
        *,
        source_channel=None,
        log_channel_id: int | None = None,
    ) -> None:
        channel_id = (
            log_channel_id
            if log_channel_id is not None
            else int(guild_config(guild.id).get("log_channel_id", 0))
        )
        channel = guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return

        embed = discord.Embed(
            title=f"{emoji('settings')} Configuration Changed",
            description=f"{actor.mention} (`{actor}`)",
            color=discord.Color(BRAND_COLOR),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_author(name=f"Changed by {actor}", icon_url=actor.display_avatar.url)
        embed.add_field(name="Setting", value=action, inline=False)
        detail_text = "\n".join(f"**{name}:** {value}" for name, value in details.items())
        if detail_text:
            embed.add_field(name="Details", value=detail_text[:1024], inline=False)
        if source_channel is not None and hasattr(source_channel, "mention"):
            embed.add_field(name="Changed in", value=source_channel.mention, inline=True)
        embed.set_thumbnail(url=emoji_url("settings"))
        embed.set_footer(text="Server configuration updated", icon_url=emoji_url("success"))
        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    async def log(self, ctx, status: str):
        if not ctx.guild or not ctx.command:
            return
        # Command logs describe actions that actually happened. Permission,
        # validation, cooldown, converter, and execution failures are not sent
        # to the guild log channel.
        if status != "completed" or getattr(ctx, "command_failed", False):
            return
        if getattr(ctx, "command_log_skip", False):
            return

        channel = await self._get_log_channel(ctx)
        if not channel:
            return

        arguments = self._arguments(ctx)
        target, target_text, target_avatar = await self._target(ctx, arguments)
        command_name = ctx.command.qualified_name
        details = []
        command_details = getattr(ctx, "command_log_details", {})

        if "duration" in arguments:
            details.append(("Duration", arguments["duration"]))
        if "seconds" in arguments:
            details.append(("Slowmode", f"{arguments['seconds']} second(s)"))
        if "amount" in arguments and "Messages deleted" not in command_details:
            details.append(("Messages requested", arguments["amount"]))
        if "role" in arguments and isinstance(arguments["role"], discord.Role):
            details.append(("Role", arguments["role"].mention))
        if "name" in arguments:
            details.append(("New nickname", arguments["name"]))

        reason = arguments.get("reason")
        if reason and reason != "No reason provided":
            details.append(("Reason", str(reason)[:500]))
        details.extend((name, value) for name, value in command_details.items())

        description = f"{ctx.author.mention} (`{ctx.author}`)"
        if target_text:
            target_name = target.name if isinstance(target, discord.Role) else str(target)
            description += f"\n\n**Target**\n{target_text} (`{target_name}`)"

        embed = discord.Embed(
            title=f"{self._icon(command_name)} {command_name.replace('_', ' ').title()}",
            description=description,
            color=discord.Color(BRAND_COLOR),
            timestamp=datetime.datetime.now(datetime.timezone.utc),
        )
        embed.set_author(name=f"Executed by {ctx.author}", icon_url=ctx.author.display_avatar.url)

        if details:
            detail_text = "\n".join(f"**{name}:** {value}" for name, value in details)
            embed.add_field(name="Details", value=detail_text[:1024], inline=False)

        embed.add_field(name="Channel", value=ctx.channel.mention, inline=True)
        message = getattr(ctx, "message", None)
        jump_url = getattr(message, "jump_url", None)
        embed.add_field(
            name="Message",
            value=f"[Jump to message]({jump_url})" if jump_url else "Interaction",
            inline=True,
        )

        if target_avatar:
            embed.set_thumbnail(url=target_avatar)
        else:
            root_name = command_name.split()[0]
            icon_name = COMMAND_ICONS.get(command_name, COMMAND_ICONS.get(root_name, "star"))
            fallback = emoji_url(icon_name)
            embed.set_thumbnail(url=fallback or (ctx.guild.icon.url if ctx.guild.icon else None))

        embed.set_footer(text="Command completed", icon_url=emoji_url("success"))
        await channel.send(embed=embed)
