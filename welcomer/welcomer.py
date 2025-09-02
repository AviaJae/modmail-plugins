import discord
from discord.ext import commands

class Welcome(commands.Cog):
    """Welcome plugin with add, list, and remove functionality, including embed support."""

    def __init__(self, bot):
        self.bot = bot
        self.welcome_messages = {}  # {guild_id: [messages]}
        self.invites = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # Cache invites at startup
        for guild in self.bot.guilds:
            try:
                self.invites[guild.id] = await guild.invites()
            except discord.Forbidden:
                self.invites[guild.id] = []

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        channel = guild.system_channel or next((c for c in guild.text_channels if c.permissions_for(guild.me).send_messages), None)
        if not channel:
            return

        # Detect invite used
        used_invite = None
        try:
            new_invites = await guild.invites()
            old_invites = self.invites.get(guild.id, [])
            for invite in new_invites:
                old_inv = discord.utils.get(old_invites, code=invite.code)
                if old_inv and invite.uses > old_inv.uses:
                    used_invite = invite
                    break
            self.invites[guild.id] = new_invites
        except discord.Forbidden:
            pass

        invite_text = f" (joined with invite `{used_invite.code}` created by {used_invite.inviter})" if used_invite else ""

        # Send all saved welcome messages
        for msg in self.welcome_messages.get(guild.id, []):
            if isinstance(msg, discord.Embed):
                embed = msg.copy()
                # Replace placeholder thumbnail
                if embed.thumbnail.url == "{avatar}":
                    embed.set_thumbnail(url=member.avatar.url if member.avatar else member.default_avatar.url)
                await channel.send(embed=embed)
            else:
                await channel.send(msg + invite_text)

    @commands.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        """Base command for managing welcome messages."""
        await ctx.send("Available subcommands: add, list, remove")

    @welcome.command(name="add")
    @commands.has_permissions(administrator=True)
    async def welcome_add(self, ctx):
        """Add a welcome message (text or embed)."""
        await ctx.send("Would you like to create an embed? (yes/no)")

        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        try:
            reply = await self.bot.wait_for("message", check=check, timeout=60)
        except:
            return await ctx.send("Timed out.")

        if reply.content.lower() in ["yes", "y"]:
            # Title
            await ctx.send("Enter the embed title:")
            title = (await self.bot.wait_for("message", check=check, timeout=60)).content

            # Description
            await ctx.send("Enter the embed description:")
            desc = (await self.bot.wait_for("message", check=check, timeout=120)).content

            # Color
            await ctx.send("Enter a hex color (e.g. #ff0000) or `none`:")
            color_msg = (await self.bot.wait_for("message", check=check, timeout=60)).content
            color = discord.Color.red() if color_msg.lower() == "none" else discord.Color(int(color_msg.strip("#"), 16))

            embed = discord.Embed(title=title, description=desc, color=color)

            # Thumbnail
            await ctx.send("Enter a thumbnail URL, type `avatar` to use member avatar, or `none`:")
            thumb_msg = (await self.bot.wait_for("message", check=check, timeout=60)).content
            if thumb_msg.lower() == "avatar":
                embed.set_thumbnail(url="{avatar}")  # placeholder, replaced on join
            elif thumb_msg.lower() != "none":
                embed.set_thumbnail(url=thumb_msg)

            # Footer
            await ctx.send("Enter footer text, or type `none`:")
            footer_msg = (await self.bot.wait_for("message", check=check, timeout=60)).content
            if footer_msg.lower() != "none":
                embed.set_footer(text=footer_msg)

            self.welcome_messages.setdefault(ctx.guild.id, []).append(embed)
            await ctx.send("✅ Embed welcome message added!")

        else:
            await ctx.send("Enter the plain text welcome message:")
            text = (await self.bot.wait_for("message", check=check, timeout=120)).content
            self.welcome_messages.setdefault(ctx.guild.id, []).append(text)
            await ctx.send("✅ Text welcome message added!")

    @welcome.command(name="list")
    @commands.has_permissions(administrator=True)
    async def welcome_list(self, ctx):
        """List all welcome messages."""
        msgs = self.welcome_messages.get(ctx.guild.id, [])
        if not msgs:
            return await ctx.send("No welcome messages set.")
        description = ""
        for i, msg in enumerate(msgs, 1):
            description += f"{i}. {'Embed' if isinstance(msg, discord.Embed) else msg[:40]}\n"
        embed = discord.Embed(title="Welcome Messages", description=description, color=discord.Color.green())
        await ctx.send(embed=embed)

    @welcome.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def welcome_remove(self, ctx, index: int):
        """Remove a welcome message by index."""
        msgs = self.welcome_messages.get(ctx.guild.id, [])
        if not msgs or index < 1 or index > len(msgs):
            return await ctx.send("Invalid index.")
        removed = msgs.pop(index - 1)
        await ctx.send(f"✅ Removed {'embed' if isinstance(removed, discord.Embed) else 'text'} welcome message.")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
