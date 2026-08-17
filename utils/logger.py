import datetime

import discord

from utils.settings import load_config
from utils.theme import BRAND, DANGER, EMOJI, SUCCESS, WARNING


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

    @staticmethod
    def _target(arguments: dict):
        for key in ("member", "user"):
            value = arguments.get(key)
            if isinstance(value, (discord.Member, discord.User)):
                return value, value.mention, value.display_avatar.url
        role = arguments.get("role")
        if isinstance(role, discord.Role):
            return role, role.mention, None
        return None, None, None

    @staticmethod
    def _color(command_name: str) -> discord.Color:
        if command_name in {"ban", "kick"}:
            return DANGER
        if command_name in {"timeout", "untimeout", "lock", "unlock"}:
            return WARNING
        if command_name in {"role", "nickname", "dumprole"}:
            return discord.Color.from_rgb(155, 89, 182)
        if command_name in {
            "help", "avatar", "banner", "say", "ping", "userinfo",
            "serverinfo", "stealemoji", "stealsticker",
        }:
            return BRAND
        return SUCCESS

    @staticmethod
    def _icon(command_name: str) -> str:
        if command_name in {"ban", "kick", "unban"}:
            return EMOJI["banhammer"]
        if command_name in {"timeout", "untimeout"}:
            return EMOJI["warning"]
        if command_name in {"role", "nickname", "dumprole"}:
            return EMOJI["roles"]
        if command_name in {"lock", "hide"}:
            return EMOJI["lock"]
        if command_name in {"unlock", "unhide"}:
            return EMOJI["unlock"]
        if command_name in {"drag", "move", "mvc", "bringall", "join"}:
            return EMOJI["arrow"]
        if command_name in {"disconnect", "mutevc", "unmutevc", "deafenvc", "undeafenvc", "vclimit", "where"}:
            return EMOJI["voice"]
        return EMOJI["sparkles"]

    async def log(self, ctx, status: str, error: Exception | None = None):
        if status != "completed" or not ctx.guild or not ctx.command or getattr(ctx, "command_failed", False):
            return

        channel_id = int(load_config().get("log_channel_id", 0))
        channel = ctx.guild.get_channel(channel_id) if channel_id else None
        if not isinstance(channel, discord.TextChannel):
            return

        arguments = self._arguments(ctx)
        target, target_text, target_avatar = self._target(arguments)
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
            title=f"{self._icon(command_name)} {command_name.replace('_', ' ').title()} Command",
            description=description,
            color=self._color(command_name),
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
        elif ctx.guild.icon:
            embed.set_thumbnail(url=ctx.guild.icon.url)

        await channel.send(embed=embed)
