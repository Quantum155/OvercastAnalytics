import discord
from discord.ext import commands


class Status(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def online(self, interaction: discord.Interaction):
        await interaction.response.send_message("I'm online!")


def setup(bot):
    bot.add_cog(Status(bot))
