import re

import discord
from discord import app_commands
from discord.ext import commands


def _id_from_argument(argument: str) -> int | None:
    match = re.fullmatch(r"<@!?(\d+)>", argument.strip())
    if match:
        return int(match.group(1))
    return int(argument) if argument.isdigit() else None


def _member_matches(guild: discord.Guild, argument: str):
    wanted = argument.removeprefix("@").casefold()
    return [
        member
        for member in guild.members
        if wanted
        in {
            member.name.casefold(),
            member.display_name.casefold(),
            (member.global_name or "").casefold(),
        }
    ]


class MemberLookup(commands.MemberConverter, app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.user

    async def transform(self, interaction: discord.Interaction, value):
        if isinstance(value, discord.Member):
            return value
        raise app_commands.TransformerError(value, discord.AppCommandOptionType.user, self)

    async def convert(self, ctx, argument: str) -> discord.Member:
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        user_id = _id_from_argument(argument)
        if user_id:
            member = ctx.guild.get_member(user_id)
            if member:
                return member
            try:
                return await ctx.guild.fetch_member(user_id)
            except (discord.NotFound, discord.HTTPException):
                pass

        matches = _member_matches(ctx.guild, argument)
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise commands.BadArgument("Multiple users have that name - use a mention or ID.")

        return await super().convert(ctx, argument)


class ChannelLookup(commands.TextChannelConverter, app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.channel

    @property
    def channel_types(self):
        return [discord.ChannelType.text, discord.ChannelType.news]

    async def transform(self, interaction: discord.Interaction, value):
        if isinstance(value, discord.TextChannel):
            return value
        raise app_commands.TransformerError(value, discord.AppCommandOptionType.channel, self)

    async def convert(self, ctx, argument: str) -> discord.TextChannel:
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        value = argument.strip()
        mention = re.fullmatch(r"<#(\d+)>", value)
        channel_id = int(mention.group(1)) if mention else int(value) if value.isdigit() else None
        if channel_id:
            channel = ctx.guild.get_channel(channel_id)
            if isinstance(channel, discord.TextChannel):
                return channel

        wanted = value.removeprefix("#").casefold()
        matches = [channel for channel in ctx.guild.text_channels if channel.name.casefold() == wanted]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise commands.BadArgument("Multiple channels have that name - use a mention or ID.")

        raise commands.ChannelNotFound(argument)


class RoleLookup(commands.RoleConverter, app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.role

    async def transform(self, interaction: discord.Interaction, value):
        return value

    async def convert(self, ctx, argument: str) -> discord.Role:
        if not ctx.guild:
            raise commands.NoPrivateMessage()

        value = argument.strip()
        mention = re.fullmatch(r"<@&(\d+)>", value)
        role_id = int(mention.group(1)) if mention else int(value) if value.isdigit() else None
        if role_id:
            role = ctx.guild.get_role(role_id)
            if role:
                return role

        wanted = value.removeprefix("@").casefold()
        matches = [role for role in ctx.guild.roles if role.name.casefold() == wanted]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise commands.BadArgument("Multiple roles have that name - use a mention or ID.")

        raise commands.RoleNotFound(argument)


class UserLookup(commands.UserConverter, app_commands.Transformer):
    @property
    def type(self) -> discord.AppCommandOptionType:
        return discord.AppCommandOptionType.user

    async def transform(self, interaction: discord.Interaction, value):
        return value

    async def convert(self, ctx, argument: str) -> discord.User:
        if ctx.guild:
            matches = _member_matches(ctx.guild, argument)
            if len(matches) == 1:
                return matches[0]
            if len(matches) > 1:
                raise commands.BadArgument("Multiple users have that name - use a mention or ID.")

        return await super().convert(ctx, argument)
