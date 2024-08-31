from discord.ext import commands
import discord

class Say(commands.Cog):
    """A simple say command that removes @everyone/@here mentions."""

    def __init__(self, bot):
        self.bot = bot

    @checks.has_permissions(PermissionLevel.ADMIN)
    @commands.command(name='say2')
    async def say2(self, ctx, channel: discord.TextChannel, *, message: str):
        """Sends a message to a specified channel, removing @everyone and @here mentions."""
        # Replace @everyone and @here mentions with a safer alternative
        filtered_message = message.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        
        # Send the filtered message to the specified channel
        await channel.send(filtered_message)
        
        # Attempt to delete the command message if the bot has permissions
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if bot doesn't have permission to delete


async def setup(bot):
    """Sets up the Say cog."""
    await bot.add_cog(Say(bot))
