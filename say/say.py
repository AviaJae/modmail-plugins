from discord.ext import commands


class Say(commands.Cog):
    """A simple say command that removes @everyone/@here mentions."""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='say2')
    async def say2(self, ctx, *, message: str):
        """Sends a message, but removes @everyone and @here mentions."""
        # Replace @everyone and @here mentions with a safer alternative
        filtered_message = message.replace("@everyone", "@\u200beveryone").replace("@here", "@\u200bhere")
        await ctx.send(filtered_message)
        
        # Attempt to delete the command message if bot has permissions
        try:
            await ctx.message.delete()
        except discord.Forbidden:
            pass  # Ignore if bot doesn't have permission to delete


async def setup(bot):
    """Sets up the Say cog."""
    await bot.add_cog(Say(bot))

