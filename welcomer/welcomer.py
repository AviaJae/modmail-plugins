import discord
from discord.ext import commands
import asyncio

class Welcome(commands.Cog):
    """Welcome system with customizable messages and embeds."""

    def __init__(self, bot):
        self.bot = bot
        self.config = {}  # Temporary in-memory storage {guild_id: {...}}

    @commands.group(invoke_without_command=True)
    async def welcome(self, ctx):
        await ctx.send("Use `welcome add`, `welcome list`, `welcome remove`, or `welcome test`.")

    @welcome.command(name="add")
    @commands.has_permissions(administrator=True)
    async def add_welcome(self, ctx):
        """Starts an interactive setup for a welcome message."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        guild_id = ctx.guild.id

        # If already exists, remove before adding
        if guild_id in self.config:
            await ctx.send("⚠️ A welcome message already exists. Removing it before creating a new one.")
            del self.config[guild_id]

        # Ask for channel
        await ctx.send("Which channel should I send the welcome message in? Mention it (e.g. #general).")
        try:
            msg = await self.bot.wait_for("message", timeout=60, check=check)
            if not msg.channel_mentions:
                await ctx.send("❌ You must mention a channel. Setup cancelled.")
                return
            channel = msg.channel_mentions[0]
        except asyncio.TimeoutError:
            await ctx.send("⏰ Setup timed out.")
            return

        # Ask if embed
        await ctx.send("Do you want the welcome message to be an **embed**? (yes/no)")
        try:
            msg = await self.bot.wait_for("message", timeout=30, check=check)
            use_embed = msg.content.lower() in ["yes", "y"]
        except asyncio.TimeoutError:
            await ctx.send("⏰ Setup timed out.")
            return

        data = {"channel_id": channel.id, "embed": use_embed}

        if use_embed:
            # Title
            await ctx.send("What should the **embed title** be?")
            try:
                msg = await self.bot.wait_for("message", timeout=60, check=check)
                data["title"] = msg.content
            except asyncio.TimeoutError:
                await ctx.send("⏰ Setup timed out.")
                return

            # Description
            await ctx.send("What should the **embed description** be?\nTip: use `{member}` to mention the new member.")
            try:
                msg = await self.bot.wait_for("message", timeout=120, check=check)
                data["description"] = msg.content
            except asyncio.TimeoutError:
                await ctx.send("⏰ Setup timed out.")
                return

            # Thumbnail (image upload)
            await ctx.send("Upload an image for the embed thumbnail.")
            try:
                msg = await self.bot.wait_for("message", timeout=60, check=check)
                if msg.attachments:
                    data["thumbnail"] = msg.attachments[0].url
                else:
                    await ctx.send("❌ No image uploaded. Setup cancelled.")
                    return
            except asyncio.TimeoutError:
                await ctx.send("⏰ Setup timed out.")
                return

            # Footer
            await ctx.send("What should the **footer text** be?")
            try:
                msg = await self.bot.wait_for("message", timeout=60, check=check)
                data["footer"] = msg.content
                await ctx.send("✅ Footer saved.")  # <-- Added confirmation so it won't look stuck
            except asyncio.TimeoutError:
                await ctx.send("⏰ Setup timed out.")
                return

        else:
            # Plain text message
            await ctx.send("What should the welcome **message** be?\nTip: use `{member}` to mention the new member.")
            try:
                msg = await self.bot.wait_for("message", timeout=120, check=check)
                data["text"] = msg.content
            except asyncio.TimeoutError:
                await ctx.send("⏰ Setup timed out.")
                return

        # Save config
        self.config[guild_id] = data
        await ctx.send("✅ Welcome message has been set up successfully!")

    @welcome.command(name="list")
    async def list_welcome(self, ctx):
        """Lists the current welcome message config."""
        data = self.config.get(ctx.guild.id)
        if not data:
            await ctx.send("ℹ️ No welcome message set.")
            return

        if data["embed"]:
            embed = discord.Embed(
                title=data.get("title", "No Title"),
                description=data.get("description", "No Description"),
                color=discord.Color.green(),
            )
            embed.set_footer(text=data.get("footer", ""))
            if "thumbnail" in data:
                embed.set_thumbnail(url=data["thumbnail"])
            await ctx.send(f"Channel: <#{data['channel_id']}>", embed=embed)
        else:
            await ctx.send(f"Channel: <#{data['channel_id']}>\nMessage: {data.get('text')}")

    @welcome.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def remove_welcome(self, ctx):
        """Removes the welcome message."""
        if ctx.guild.id in self.config:
            del self.config[ctx.guild.id]
            await ctx.send("🗑️ Welcome message removed.")
        else:
            await ctx.send("ℹ️ No welcome message set.")

    @welcome.command(name="test")
    async def test_welcome(self, ctx):
        """Tests the welcome message. Pings runner if no member is available."""
        data = self.config.get(ctx.guild.id)
        if not data:
            await ctx.send("ℹ️ No welcome message set.")
            return

        channel = ctx.guild.get_channel(data["channel_id"])
        member = ctx.author  # For test, always use the runner

        if data["embed"]:
            embed = discord.Embed(
                title=data.get("title", "No Title"),
                description=data.get("description", "").replace("{member}", member.mention),
                color=discord.Color.green(),
            )
            embed.set_footer(text=data.get("footer", ""))
            if "thumbnail" in data:
                embed.set_thumbnail(url=data["thumbnail"])
            await channel.send(member.mention, embed=embed)
        else:
            text = data.get("text", "").replace("{member}", member.mention)
            await channel.send(text)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        """Sends the welcome message when a new member joins."""
        data = self.config.get(member.guild.id)
        if not data:
            return

        channel = member.guild.get_channel(data["channel_id"])
        if not channel:
            return

        # Find invite used
        invite_used = "Unknown"
        try:
            invites_before = await member.guild.invites()
            # Note: To properly track invites, you’d need to cache invites before/after join
            invite_used = invites_before[0].url if invites_before else "Unknown"
        except Exception:
            pass

        if data["embed"]:
            embed = discord.Embed(
                title=data.get("title", "No Title"),
                description=data.get("description", "").replace("{member}", member.mention)
                              + f"\nJoined with invite: {invite_used}",
                color=discord.Color.green(),
            )
            embed.set_footer(text=data.get("footer", ""))
            if "thumbnail" in data:
                embed.set_thumbnail(url=data["thumbnail"])
            await channel.send(member.mention, embed=embed)
        else:
            text = data.get("text", "").replace("{member}", member.mention)
            text += f"\nJoined with invite: {invite_used}"
            await channel.send(text)


async def setup(bot):
    await bot.add_cog(Welcome(bot))
