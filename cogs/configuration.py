import discord
from discord.ext import commands

from utils.cog import BaseCog
from utils.settings import CONFIGURABLE_COMMANDS, guild_config, update_guild_config
from utils.theme import BRAND, emoji, partial_emoji

DEFAULT_PREFIX = "!"

COMMAND_EMOJIS = {
    "dumprole": "folder",
    "purge": "clear",
    "role": "role_add",
    "say": "reply",
    "stealemoji": "emoji",
    "stealsticker": "sticker",
    "temprole": "role_add",
}


def command_emoji(command_name: str):
    return partial_emoji(COMMAND_EMOJIS.get(command_name, command_name))


PERMISSION_SECTIONS = {
    "moderation": ("Moderation", "shield", ["kick", "ban", "unban", "timeout", "untimeout", "purge"]),
    "channels": ("Channels", "lock", ["lock", "unlock", "hide", "unhide", "slowmode"]),
    "members": ("Members and roles", "role_add", ["role", "temprole", "nickname", "dumprole"]),
    "voice": (
        "Voice",
        "mvc",
        [
            "drag", "move", "mvc", "bringall", "join", "disconnect", "mutevc",
            "unmutevc", "deafenvc", "undeafenvc", "vclimit", "where",
        ],
    ),
    "general": ("General", "settings", ["avatar", "banner", "say", "ping", "stealemoji", "stealsticker"]),
}

CATEGORIES = [
    ("overview", "Overview", "settings"),
    ("prefix", "Prefix", "settings"),
    ("admin_role", "Admin role", "role_add"),
    ("log_channel", "Log channel", "folder"),
    ("command_permissions", "Command permissions", "shield"),
]


async def log_config_change(
    interaction: discord.Interaction,
    action: str,
    details: dict,
    *,
    log_channel_id: int | None = None,
):
    logger = getattr(interaction.client, "command_logger", None)
    if logger is not None:
        await logger.log_config_change(
            interaction.guild,
            interaction.user,
            action,
            details,
            source_channel=interaction.channel,
            log_channel_id=log_channel_id,
        )


def config_access():
    async def check(ctx):
        if not ctx.guild:
            raise commands.NoPrivateMessage()
        if (
            await ctx.bot.is_owner(ctx.author)
            or ctx.author.id == ctx.guild.owner_id
            or ctx.author.guild_permissions.administrator
        ):
            return True
        raise commands.MissingPermissions(["administrator"])

    return commands.check(check)


# ---------------------------------------------------------------------------
# Embeds — one small, focused embed per screen instead of one giant one.
# ---------------------------------------------------------------------------

def _base_embed(title_key: str, title: str, description: str) -> discord.Embed:
    embed = discord.Embed(title=f"{emoji(title_key)} {title}", description=description, color=BRAND)
    embed.set_footer(text="Only the person who opened this panel can use its controls.")
    return embed


def overview_embed(guild: discord.Guild) -> discord.Embed:
    settings = guild_config(guild.id)
    admin_role_id = int(settings.get("admin_role_id", 0))
    log_channel_id = int(settings.get("log_channel_id", 0))
    configured = sum(1 for ids in settings.get("command_role_ids", {}).values() if ids)

    embed = _base_embed("settings", "Server configuration", "Pick what you'd like to configure below.")
    embed.add_field(name="Prefix", value=f"`{settings.get('prefix', DEFAULT_PREFIX)}`", inline=True)
    embed.add_field(name="Admin role", value=f"<@&{admin_role_id}>" if admin_role_id else "*Not set*", inline=True)
    embed.add_field(name="Log channel", value=f"<#{log_channel_id}>" if log_channel_id else "*Not set*", inline=True)
    embed.add_field(
        name="Command permissions",
        value=f"{configured} command(s) have custom roles" if configured else "None set — admins only",
        inline=False,
    )
    return embed


def prefix_embed(guild: discord.Guild) -> discord.Embed:
    prefix = guild_config(guild.id).get("prefix", DEFAULT_PREFIX)
    embed = _base_embed("settings", "Prefix", "The prefix used for text commands in this server.")
    embed.add_field(name="Current prefix", value=f"`{prefix}`")
    return embed


def admin_role_embed(guild: discord.Guild) -> discord.Embed:
    role_id = int(guild_config(guild.id).get("admin_role_id", 0))
    embed = _base_embed(
        "role_add", "Admin role",
        "Members with this role are treated as bot admins, in addition to server admins.",
    )
    embed.add_field(name="Current role", value=f"<@&{role_id}>" if role_id else "*Not set*")
    return embed


def log_channel_embed(guild: discord.Guild) -> discord.Embed:
    channel_id = int(guild_config(guild.id).get("log_channel_id", 0))
    embed = _base_embed("folder", "Log channel", "Where command usage gets logged.")
    embed.add_field(name="Current channel", value=f"<#{channel_id}>" if channel_id else "*Not set*")
    return embed


def command_permissions_embed(guild: discord.Guild, command_name: str | None) -> discord.Embed:
    embed = _base_embed(
        "shield", "Command permissions",
        "Choose a section, choose a command, then pick every allowed role. Changes save instantly.",
    )
    if not command_name:
        embed.add_field(name="Command", value="*Choose one below to continue*", inline=False)
        return embed

    role_ids = guild_config(guild.id).get("command_role_ids", {}).get(command_name, [])
    roles = [guild.get_role(rid) for rid in role_ids]
    mentions = "\n".join(f"• {r.mention}" for r in roles if r is not None)
    missing = sum(1 for r in roles if r is None)
    if missing:
        mentions += f"\n• {missing} deleted role(s)"

    embed.add_field(name="Command", value=f"`/{command_name}`", inline=False)
    embed.add_field(
        name="Allowed roles",
        value=mentions.strip()[:1024] or "*No extra roles — admins only for now*",
        inline=False,
    )
    return embed


EMBED_BUILDERS = {
    "overview": lambda v: overview_embed(v.guild),
    "prefix": lambda v: prefix_embed(v.guild),
    "admin_role": lambda v: admin_role_embed(v.guild),
    "log_channel": lambda v: log_channel_embed(v.guild),
    "command_permissions": lambda v: command_permissions_embed(v.guild, v.command_name),
}


# ---------------------------------------------------------------------------
# Components
# ---------------------------------------------------------------------------

class PrefixModal(discord.ui.Modal, title="Change server prefix"):
    prefix = discord.ui.TextInput(label="New prefix", placeholder="Example: !", min_length=1, max_length=5)

    def __init__(self, view: "ConfigView"):
        super().__init__()
        self.view_ref = view
        self.prefix.default = guild_config(view.guild.id).get("prefix", DEFAULT_PREFIX)

    async def on_submit(self, interaction: discord.Interaction):
        new_prefix = str(self.prefix)
        if any(character.isspace() for character in new_prefix):
            await interaction.response.send_message("The prefix cannot contain spaces.", ephemeral=True)
            return
        old_prefix = guild_config(self.view_ref.guild.id).get("prefix", DEFAULT_PREFIX)
        if new_prefix != old_prefix:
            update_guild_config(self.view_ref.guild.id, prefix=new_prefix)
            await log_config_change(
                interaction,
                "Prefix",
                {"Before": f"`{old_prefix}`", "After": f"`{new_prefix}`"},
            )
        await interaction.response.edit_message(embed=prefix_embed(self.view_ref.guild), view=self.view_ref)


class CategorySelect(discord.ui.Select):
    def __init__(self, current: str):
        options = [
            discord.SelectOption(label=label, value=key, emoji=partial_emoji(icon), default=key == current)
            for key, label, icon in CATEGORIES
        ]
        super().__init__(placeholder="What would you like to configure?", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        view.category = self.values[0]
        view.command_name = None
        view.rebuild()
        await interaction.response.edit_message(embed=EMBED_BUILDERS[view.category](view), view=view)


class AdminRoleSelect(discord.ui.RoleSelect):
    def __init__(self, guild: discord.Guild):
        current_id = int(guild_config(guild.id).get("admin_role_id", 0))
        current_role = guild.get_role(current_id) if current_id else None
        super().__init__(
            placeholder="Choose the admin role",
            min_values=0,
            max_values=1,
            row=1,
            default_values=[current_role] if current_role else [],
        )

    async def callback(self, interaction: discord.Interaction):
        old_id = int(guild_config(interaction.guild_id).get("admin_role_id", 0))
        role_id = self.values[0].id if self.values else 0
        if role_id != old_id:
            update_guild_config(interaction.guild_id, admin_role_id=role_id)
            await log_config_change(
                interaction,
                "Admin role",
                {
                    "Before": f"<@&{old_id}>" if old_id else "Not set",
                    "After": f"<@&{role_id}>" if role_id else "Not set",
                },
            )
        await interaction.response.edit_message(embed=admin_role_embed(self.view.guild), view=self.view)


class LogChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, guild: discord.Guild):
        current_id = int(guild_config(guild.id).get("log_channel_id", 0))
        current_channel = guild.get_channel(current_id) if current_id else None
        super().__init__(
            placeholder="Choose the log channel",
            channel_types=[discord.ChannelType.text, discord.ChannelType.news],
            min_values=0,
            max_values=1,
            row=1,
            default_values=[current_channel] if current_channel else [],
        )

    async def callback(self, interaction: discord.Interaction):
        old_id = int(guild_config(interaction.guild_id).get("log_channel_id", 0))
        channel_id = self.values[0].id if self.values else 0
        if channel_id != old_id:
            update_guild_config(interaction.guild_id, log_channel_id=channel_id)
            await log_config_change(
                interaction,
                "Log channel",
                {
                    "Before": f"<#{old_id}>" if old_id else "Not set",
                    "After": f"<#{channel_id}>" if channel_id else "Not set",
                },
                log_channel_id=channel_id or old_id,
            )
        await interaction.response.edit_message(embed=log_channel_embed(self.view.guild), view=self.view)


class CommandSelect(discord.ui.Select):
    def __init__(self, current: str | None, section: str):
        page_names = PERMISSION_SECTIONS[section][2]
        options = [
            discord.SelectOption(
                label=name.replace("_", " ").title(),
                value=name,
                emoji=command_emoji(name),
                default=name == current,
            )
            for name in page_names
        ]
        super().__init__(
            placeholder="2. Choose a command",
            options=options,
            row=2,
        )

    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        view.command_name = self.values[0]
        view.rebuild()
        await interaction.response.edit_message(
            embed=command_permissions_embed(view.guild, view.command_name), view=view
        )


class PermissionSectionSelect(discord.ui.Select):
    def __init__(self, current: str):
        options = [
            discord.SelectOption(
                label=label,
                value=key,
                emoji=partial_emoji(icon),
                default=key == current,
            )
            for key, (label, icon, command_names) in PERMISSION_SECTIONS.items()
        ]
        super().__init__(placeholder="1. Choose a command section", options=options, row=1)

    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        view.command_section = self.values[0]
        view.command_name = None
        view.rebuild()
        await interaction.response.edit_message(
            embed=command_permissions_embed(view.guild, None),
            view=view,
        )


class CommandRoleSelect(discord.ui.RoleSelect):
    def __init__(self, guild: discord.Guild, command_name: str):
        role_ids = guild_config(guild.id).get("command_role_ids", {}).get(command_name, [])
        current_roles = [guild.get_role(rid) for rid in role_ids if guild.get_role(rid)]
        super().__init__(
            placeholder=f"Roles allowed to use /{command_name}",
            min_values=0,
            max_values=25,
            row=3,
            default_values=current_roles,
        )
        self.command_name = command_name

    async def callback(self, interaction: discord.Interaction):
        view: ConfigView = self.view
        settings = guild_config(view.guild.id)
        command_roles = {name: list(ids) for name, ids in settings.get("command_role_ids", {}).items()}
        old_role_ids = command_roles.get(self.command_name, [])
        old_roles = " ".join(f"<@&{role_id}>" for role_id in old_role_ids) or "Administrator access only"
        new_role_ids = sorted(role.id for role in self.values)
        new_roles = " ".join(role.mention for role in self.values) or "Administrator access only"
        if sorted(old_role_ids) != new_role_ids:
            command_roles[self.command_name] = new_role_ids
            update_guild_config(view.guild.id, command_role_ids=command_roles)
            await log_config_change(
                interaction,
                "Command permissions",
                {
                    "Command": f"`/{self.command_name}`",
                    "Before": old_roles,
                    "After": new_roles,
                },
            )
        await interaction.response.edit_message(
            embed=command_permissions_embed(view.guild, self.command_name), view=view
        )


# ---------------------------------------------------------------------------
# The view — one small set of controls per category, rebuilt on switch.
# ---------------------------------------------------------------------------

class ConfigView(discord.ui.View):
    def __init__(self, requester_id: int, guild: discord.Guild):
        super().__init__(timeout=300)
        self.requester_id = requester_id
        self.guild = guild
        self.message: discord.Message | None = None
        self.category = "overview"
        self.command_name = None
        self.command_section = "moderation"
        self.rebuild()

    def rebuild(self):
        self.clear_items()
        self.add_item(CategorySelect(self.category))

        if self.category == "prefix":
            self.add_item(self._button("Change prefix", discord.ButtonStyle.primary, "settings", self.change_prefix))
            self.add_item(self._button("Reset to default", discord.ButtonStyle.secondary, "fail", self.reset_prefix))
        elif self.category == "admin_role":
            self.add_item(AdminRoleSelect(self.guild))
        elif self.category == "log_channel":
            self.add_item(LogChannelSelect(self.guild))
        elif self.category == "command_permissions":
            self.add_item(PermissionSectionSelect(self.command_section))
            self.add_item(CommandSelect(self.command_name, self.command_section))
            if self.command_name:
                self.add_item(CommandRoleSelect(self.guild, self.command_name))

        self.add_item(self._button("Close", discord.ButtonStyle.secondary, "success", self.close, row=4))

    def _button(self, label, style, icon, callback, row=3, disabled=False):
        button = discord.ui.Button(
            label=label,
            style=style,
            emoji=partial_emoji(icon),
            row=row,
            disabled=disabled,
        )
        button.callback = callback
        return button

    async def change_prefix(self, interaction: discord.Interaction):
        await interaction.response.send_modal(PrefixModal(self))

    async def reset_prefix(self, interaction: discord.Interaction):
        old_prefix = guild_config(self.guild.id).get("prefix", DEFAULT_PREFIX)
        if old_prefix != DEFAULT_PREFIX:
            update_guild_config(self.guild.id, prefix=DEFAULT_PREFIX)
            await log_config_change(
                interaction,
                "Prefix reset",
                {"Before": f"`{old_prefix}`", "After": f"`{DEFAULT_PREFIX}`"},
            )
        await interaction.response.edit_message(embed=prefix_embed(self.guild), view=self)

    async def close(self, interaction: discord.Interaction):
        for item in self.children:
            item.disabled = True
        await interaction.response.edit_message(embed=overview_embed(self.guild), view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.requester_id:
            return True
        await interaction.response.send_message("This configuration panel belongs to someone else.", ephemeral=True)
        return False

    async def on_timeout(self):
        for item in self.children:
            item.disabled = True
        if self.message:
            try:
                await self.message.edit(view=self)
            except discord.HTTPException:
                pass


class Configuration(BaseCog):
    @commands.hybrid_command(name="config", description="Open the interactive server configuration panel.")
    @config_access()
    async def config(self, ctx):
        ctx.command_log_skip = True
        view = ConfigView(ctx.author.id, ctx.guild)
        view.message = await ctx.reply(embed=overview_embed(ctx.guild), view=view, mention_author=False)


async def setup(bot):
    await bot.add_cog(Configuration(bot))
