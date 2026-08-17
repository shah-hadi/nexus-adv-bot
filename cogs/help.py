if __name__ == "__main__":
    raise SystemExit("This is a command module. Start the bot with: python main.py")

import discord
from discord.ext import commands

from utils.settings import load_config
from utils.theme import BRAND, EMOJI

CREDITS_FOOTER = f"Built with {EMOJI['heart']} by Shah Hadi"

class HelpMenu(discord.ui.View):
    def __init__(self, requester_id: int, prefix: str, bot: commands.Bot):
        super().__init__(timeout=300)
        self.requester_id = requester_id
        self.prefix = prefix
        self.bot = bot
        self.add_item(HelpSelector(self))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.requester_id:
            return True
        embed = discord.Embed(description=f"{EMOJI['wrong']} This help menu belongs to someone else.", color=discord.Color.red())
        await interaction.response.send_message(embed=embed, ephemeral=True)
        return False

    def page(self, section: str) -> discord.Embed:
        p = self.prefix
        pages = {
            "home": {
                "title": f"{EMOJI['sparkles']} Help Center",
                "description": "Select a category below to view commands and their usage.",
                "fields": [
                    ("Moderation", "Member actions, timeouts, and message cleanup."),
                    ("Channels and Members", "Channel access, roles, and nicknames."),
                    ("Voice Controls", "Voice movement and moderation tools."),
                    ("Information and Utilities", "Profiles, server details, assets, and owner tools."),
                ],
            },
            "moderation": {
                "title": f"{EMOJI['moderation']} Moderation Commands",
                "description": "Arguments in `[brackets]` are optional.",
                "fields": [
                    ("Member Actions", f"`{p}kick <member> [reason]`\n`{p}ban <user|id> [reason]`\n`{p}unban <user-id> [reason]`"),
                    ("Timeouts", f"`{p}timeout <member> <duration> [reason]`\n`{p}untimeout <member> [reason]`\nAliases: `{p}mute`, `{p}to`, `{p}unmute`, `{p}rto`"),
                    ("Message Cleanup", f"`{p}clear <amount> [member]`\nDeletes 1–100 messages; optionally filter by member."),
                ],
            },
            "channels": {
                "title": f"{EMOJI['lock']} Channels and Members",
                "description": "Channel arguments accept a mention, ID, or name.",
                "fields": [
                    ("Channel Access", f"`{p}lock [channel]` • `{p}unlock [channel]`\n`{p}hide [channel]` • `{p}unhide [channel]`\n`{p}slowmode <seconds>`"),
                    ("Roles and Nicknames", f"`{p}role <member> <role>` — toggle a role\n`{p}temprole <member> <role> <duration> [reason]`\n`{p}nickname <member> <name>` — alias: `{p}nick`"),
                ],
            },
            "voice": {
                "title": f"{EMOJI['voice']} Voice Controls",
                "description": "Voice actions require the appropriate Discord permissions.",
                "fields": [
                    ("Movement", f"`{p}drag <member>` — move to your VC\n`{p}move <member> <voice-channel>`\n`{p}mvc <source> <destination>`\n`{p}bringall <source>` • `{p}join <member>`"),
                    ("Voice Moderation", f"`{p}disconnect <member>` — alias: `{p}dc`\n`{p}mutevc <member>` • `{p}unmutevc <member>`\n`{p}deafenvc <member>` • `{p}undeafenvc <member>`\n`{p}vclimit <voice-channel> <limit>`"),
                    ("Member Location", f"`{p}where <member>` — aliases: `{p}kh`, `{p}wv`"),
                ],
            },
            "access": {
                "title": f"{EMOJI['roles']} Information and Utilities",
                "description": "Profile, server, asset, and owner utilities.",
                "fields": [
                    ("Information", f"`{p}user [member]` • `{p}server`\n`{p}dumprole <role>`"),
                    ("Utilities", f"`{p}av [user]` • `{p}banner [user]`\n`{p}say <message>` • `{p}ping`"),
                    ("Server Assets", f"`{p}stealemoji <emoji>`\n`{p}stealsticker` — reply to a sticker"),
                    ("Owner Access", f"`{p}noprefix <user> <add|remove>`"),
                ],
            },
        }
        data = pages[section]
        embed = discord.Embed(title=data["title"], description=data["description"], color=BRAND)
        if self.bot.user:
            embed.set_thumbnail(url=self.bot.user.display_avatar.url)
        for name, value in data["fields"]:
            embed.add_field(name=name, value=value, inline=False)
        embed.add_field(name="\u200b", value=CREDITS_FOOTER, inline=False)
        embed.set_footer(text="Select another section below to continue.")
        return embed


class HelpSelector(discord.ui.Select):
    def __init__(self, menu: HelpMenu):
        self.menu = menu
        options = [
            discord.SelectOption(label="Main Menu", value="home", description="Return to the overview", emoji=EMOJI["sparkles"]),
            discord.SelectOption(label="Moderation", value="moderation", description="Bans, timeouts, cleanup", emoji=EMOJI["moderation"]),
            discord.SelectOption(label="Channels and Members", value="channels", description="Access, roles, and nicknames", emoji=EMOJI["lock"]),
            discord.SelectOption(label="Voice Controls", value="voice", description="Move and find voice members", emoji=EMOJI["voice"]),
            discord.SelectOption(label="Access and Information", value="access", description="Role lists, profiles, owner tools", emoji=EMOJI["roles"]),
        ]
        super().__init__(placeholder="Choose a help section", min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.edit_message(embed=self.menu.page(self.values[0]), view=self.menu)


class Help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.hybrid_command(name="help", description="Open the interactive command guide.")
    async def help(self, ctx):
        prefix = load_config().get("prefix", "!")
        menu = HelpMenu(ctx.author.id, prefix, self.bot)
        await ctx.reply(
            embed=menu.page("home"),
            view=menu,
            mention_author=False,
            allowed_mentions=discord.AllowedMentions.none(),
        )


async def setup(bot):
    await bot.add_cog(Help(bot))
