if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import discord
from discord.ext import commands
from discord.utils import utcnow

from utils.settings import guild_config
from utils.theme import BRAND_COLOR, emoji, partial_emoji


CREDITS_FOOTER = f"**Built with {emoji('love')} by Rectrict**"

# Icon shown in the title of each section.
SECTION_ICON = {
    "home": "home",
    "moderation": "shield",
    "channels": "lock",
    "voice": "mvc",
    "access": "folder",
}

SECTION_LABELS = {
    "home": "Main Menu",
    "moderation": "Moderation",
    "channels": "Channels and Members",
    "voice": "Voice Controls",
    "access": "Access and Information",
}


class HelpMenu(discord.ui.View):
    """Interactive, dropdown-driven help menu."""

    def __init__(self, requester_id: int, prefix: str, bot: commands.Bot):
        super().__init__(timeout=300)
        self.requester_id = requester_id
        self.prefix = prefix
        self.bot = bot
        self.current_section = "home"

        self.selector = HelpSelector(self)
        self.add_item(self.selector)
        self.sync_controls()

    def sync_controls(self) -> None:
        """Keep the dropdown's shown value in sync with whatever section is
        currently on screen."""
        for option in self.selector.options:
            option.default = option.value == self.current_section

    async def show(self, interaction: discord.Interaction, section: str) -> None:
        self.current_section = section
        embed = self.page(section)
        self.sync_controls()
        await interaction.response.edit_message(embed=embed, view=self)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.requester_id:
            return True
        embed = discord.Embed(
            description=f"{emoji('fail')} This help menu belongs to someone else.",
            color=BRAND_COLOR,
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True

    # -- Page building -----------------------------------------------------
    # Each section has its own small builder so `page()` only ever builds
    # the embed the user actually asked to see, instead of constructing
    # every section's fields on every single click.

    def page(self, section: str) -> discord.Embed:
        icon = emoji(SECTION_ICON[section])
        title, description, fields = getattr(self, f"_build_{section}")(icon)
        return self._render(title, description, fields)

    def _render(self, title: str, description: str, fields: list[tuple[str, str]]) -> discord.Embed:
        embed = discord.Embed(
            title=title,
            description=description,
            color=BRAND_COLOR,
            timestamp=utcnow(),
        )
        if self.bot.user:
            embed.set_author(name=f"{self.bot.user.name} Help Menu", icon_url=self.bot.user.display_avatar.url)
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)

        for name, value in fields:
            embed.add_field(name=name, value=value, inline=False)

        embed.add_field(name="\u200b", value=CREDITS_FOOTER, inline=False)

        footer_icon = self.bot.user.display_avatar.url if self.bot.user else None
        embed.set_footer(text=f"{self.prefix}help  •  Select another section below to continue.", icon_url=footer_icon)
        return embed

    @staticmethod
    def _lines(*rows: tuple[str, str, str]) -> str:
        """Build a simple 'emoji `command` — description' list, one per line."""
        return "\n".join(f"{emoji(icon)} `{cmd}` — {desc}" for icon, cmd, desc in rows)

    def _build_home(self, icon: str):
        title = f"{icon}  Help Center"
        description = "Pick a category from the dropdown below to see its commands."
        fields = [
            (f"{emoji('shield')}  Moderation", "Member actions, timeouts, and message cleanup."),
            (f"{emoji('lock')}  Channels and Members", "Channel access, roles, and nicknames."),
            (f"{emoji('mvc')}  Voice Controls", "Voice movement and moderation tools."),
            (f"{emoji('folder')}  Access and Information", "Profiles, server details, assets, and owner tools."),
        ]
        return title, description, fields

    def _build_moderation(self, icon: str):
        p = self.prefix
        title = f"{icon}  Moderation Commands"
        lines = self._lines(
            ("kick", f"{p}kick <member> [reason]", "Kick a member"),
            ("ban", f"{p}ban <user|id> [reason]", "Ban a user"),
            ("unban", f"{p}unban <user-id> [reason]", "Unban a user"),
            ("timeout", f"{p}timeout <member> <duration>", "Timeout a member"),
            ("untimeout", f"{p}untimeout <member> [reason]", "Remove a timeout"),
            ("clear", f"{p}clear <amount> [member]", "Bulk-delete messages"),
        )
        return title, lines, []

    def _build_channels(self, icon: str):
        p = self.prefix
        title = f"{icon}  Channels and Members"
        lines = self._lines(
            ("lock", f"{p}lock [channel]", "Lock a channel"),
            ("unlock", f"{p}unlock [channel]", "Unlock a channel"),
            ("hide", f"{p}hide [channel]", "Hide a channel"),
            ("unhide", f"{p}unhide [channel]", "Unhide a channel"),
            ("slowmode", f"{p}slowmode <seconds>", "Set channel slowmode"),
            ("role_add", f"{p}role <member> <role>", "Add or remove a role"),
            ("nickname", f"{p}nickname <member> <name>", "Change a nickname"),
        )
        return title, lines, []

    def _build_voice(self, icon: str):
        p = self.prefix
        title = f"{icon}  Voice Controls"
        lines = self._lines(
            ("drag", f"{p}drag <member>", "Drag a member to your VC"),
            ("move", f"{p}move <member> <vc>", "Move a member"),
            ("mvc", f"{p}mvc <source> <destination>", "Move an entire VC"),
            ("bringall", f"{p}bringall <source>", "Bring everyone from a VC"),
            ("join", f"{p}join <member>", "Join a member's VC"),
            ("disconnect", f"{p}disconnect <member>", "Disconnect a member"),
            ("mutevc", f"{p}mutevc <member>", "Server mute"),
            ("unmutevc", f"{p}unmutevc <member>", "Remove server mute"),
            ("deafenvc", f"{p}deafenvc <member>", "Server deafen"),
            ("undeafenvc", f"{p}undeafenvc <member>", "Remove server deafen"),
            ("vclimit", f"{p}vclimit <vc> <limit>", "Set a VC user limit"),
            ("where", f"{p}where <member>", "Find a member's VC"),
        )
        return title, lines, []

    def _build_access(self, icon: str):
        p = self.prefix
        title = f"{icon}  Access and Information"
        lines = self._lines(
            ("info", f"{p}user [member]", "View a user's info"),
            ("info", f"{p}server", "View server info"),
            ("folder", f"{p}dumprole <role>", "List members with a role"),
            ("avatar", f"{p}av [user]", "View an avatar"),
            ("banner", f"{p}banner [user]", "View a banner"),
            ("ping", f"{p}ping", "Check bot latency"),
            ("reply", f"{p}say <message>", "Make the bot say something"),
            ("emoji", f"{p}stealemoji <emoji>", "Steal an emoji"),
            ("sticker", f"{p}stealsticker", "Steal a sticker (reply to it)"),
            ("settings", f"{p}config", "Admin: manage all server settings"),
        )
        return title, lines, []


class HelpSelector(discord.ui.Select):
    def __init__(self, menu: HelpMenu):
        self.menu = menu
        options = [
            discord.SelectOption(
                label=SECTION_LABELS["home"], value="home",
                description="Return to the overview",
                emoji=partial_emoji("home"),
            ),
            discord.SelectOption(
                label=SECTION_LABELS["moderation"], value="moderation",
                description="Bans, timeouts, cleanup",
                emoji=partial_emoji("shield"),
            ),
            discord.SelectOption(
                label=SECTION_LABELS["channels"], value="channels",
                description="Access, roles, and nicknames",
                emoji=partial_emoji("lock"),
            ),
            discord.SelectOption(
                label=SECTION_LABELS["voice"], value="voice",
                description="Move and find voice members",
                emoji=partial_emoji("mvc"),
            ),
            discord.SelectOption(
                label=SECTION_LABELS["access"], value="access",
                description="Role lists, profiles, owner tools",
                emoji=partial_emoji("folder"),
            ),
        ]
        super().__init__(placeholder="Choose a help section", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        await self.menu.show(interaction, self.values[0])


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Open the interactive command guide.")
    async def help(self, ctx):
        prefix = guild_config(ctx.guild.id if ctx.guild else None).get("prefix", "!")
        menu = HelpMenu(ctx.author.id, prefix, self.bot)
        await ctx.reply(
            embed=menu.page("home"),
            view=menu,
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot):
    await bot.add_cog(Help(bot))
