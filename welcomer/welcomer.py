import discord
from discord.ext import commands

class Welcome(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # {guild_id: {"channel": channel_id, "message": text/embed}}
        self.welcome_data = {}
        self.invites = {}

    # ... [on_ready, on_member_join stay the same] ...

    @commands.group(name="welcome", invoke_without_command=True)
    @commands.has_permissions(administrator=True)
    async def welcome(self, ctx):
        """Base command for managing welcome messages."""
        await ctx.send("Available subcommands: add, remove, test")

    # ---------------- TEST COMMAND ----------------
    @welcome.command(name="test")
    @commands.has_permissions(administrator=True)
    async def welcome_test(self, ctx):
        """Simulates a welcome message."""
        guild = ctx.guild
        data = self.welcome_data.get(guild.id)
        if not data:
            return await ctx.send("No welcome message set up.")

        channel = guild.get_channel(data.get("channel"))
        if not channel or not channel.permissions_for(guild.me).send_messages:
            return await ctx.send("I don't have permission to send messages in the welcome channel.")

        # Pick who to ping: use ctx.author if no "real" member
        fake_member = ctx.author  

        # Fake invite info
        invite_text = "(Joined with test invite `abc123` created by TestUser)"

        # Send test
        await channel.send(fake_member.mention)
        msg = data.get("message")
        if isinstance(msg, discord.Embed):
            embed = msg.copy()
            embed.add_field(name="Invite Info", value=invite_text, inline=False)
            await channel.send(embed=embed)
        else:
            await channel.send(msg + "\n" + invite_text)

        await ctx.send("✅ Sent test welcome message.")

    # ---------------- REMOVE COMMAND ----------------
    @welcome.command(name="remove")
    @commands.has_permissions(administrator=True)
    async def welcome_remove(self, ctx):
        """Remove the current welcome message."""
        if ctx.guild.id not in self.welcome_data:
            return await ctx.send("No welcome message set for this server.")
        self.welcome_data.pop(ctx.guild.id)
        await ctx.send("✅ Welcome message removed.")

    # ---------------- ADD COMMAND ----------------
    @welcome.command(name="add")
    @commands.has_permissions(administrator=True)
    async def welcome_add(self, ctx):
        """Add a welcome message (text or embed)."""
        def check(m):
            return m.author == ctx.author and m.channel == ctx.channel

        # Ask for channel
        await ctx.send("Mention the channel where welcomes should be sent:")
        try:
            reply = await self.bot.wait_for("message", check=check, timeout=60)
        except:
            return await ctx.send("Timed out.")
        if not reply.channel_mentions:
            return await ctx.send("You must mention a valid channel.")
        channel = reply.channel_mentions[0]

        # Ask for embed or text
        await ctx.send("Would you like to create an embed? (yes/no)")
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

            # Thumbnail (upload file)
            await ctx.send("Upload an image for the thumbnail, or type `none`:")
            thumb_msg = await self.bot.wait_for("message", check=check, timeout=60)
            if thumb_msg.attachments:
                embed.set_thumbnail(url=thumb_msg.attachments[0].url)
            elif thumb_msg.content.lower() != "none":
                try:
                    embed.set_thumbnail(url=thumb_msg.content)
                except:
                    pass

            # Footer
            await ctx.send("Enter footer text, or type `none`:")
            footer_msg = (await self.bot.wait_for("message", check=check, timeout=60)).content
            if footer_msg.lower() != "none":
                embed.set_footer(text=footer_msg)

            # Save (replace existing)
            self.welcome_data[guild.id] = {"channel": channel.id, "message": embed}
            await ctx.send("✅ Embed welcome message added!")

        else:
            # Plain text
            await ctx.send("Enter the plain text welcome message:")
            text = (await self.bot.wait_for("message", check=check, timeout=120)).content

            # Save (replace existing)
            self.welcome_data[guild.id] = {"channel": channel.id, "message": text}
            await ctx.send("✅ Text welcome message added!")

async def setup(bot):
    await bot.add_cog(Welcome(bot))
