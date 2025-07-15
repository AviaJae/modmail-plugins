import discord
from discord.ext import commands

class Say(commands.Cog):
    """A simple say command that removes @everyone/@here mentions and supports attachments."""

    def __init__(self, bot):
        self.bot = bot

    @commands.has_permissions(administrator=True)
    @commands.command(name='say2')
    async def say2(self, ctx, *, message: str = ""):
        """Sends a message, but removes @everyone and @here mentions and includes attachments."""
        # Replace @everyone and @here with safe versions
        filtered_message = message.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")

        # Collect any attachments
        files = []
        for attachment in ctx.message.attachments:
            file = await attachment.to_file()
            files.append(file)

        # Send the sanitized message and attachments
        await ctx.send(filtered_message, files=files if files else None)

        # Attempt to delete the original command message
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass

    @say2.error
    async def say2_error(self, ctx, error):
        """Handles errors for the say2 command."""
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("You do not have permission to use this command.", delete_after=10)
        else:
            raise error

async def setup(bot):
    """Sets up the Say cog."""
    await bot.add_cog(Say(bot))
