import discord
from discord.ext import commands
import pathlib
import json


class SetNotifications(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = pathlib.Path("config")
        self.config.touch()

    @discord.slash_command()
    async def set_notifications(self, interaction: discord.Interaction, group: discord.Role, after: int, repeat_every: int):
        """
        Set notification settings for a server.
        :param interaction: (Provided by discord)
        :param group: Discord role that will be mentioned
        :param after: Seconds of gametime after which notifications should be sent
        :param repeat_every: After the first notification, repeat every X seconds
        """
        with open(self.config, "r") as file:
            configs = json.load(file)

        configs[interaction.guild_id] = {"group": group.id, "after": after, "repeat": repeat_every}

        with open(self.config, "w") as file:
            json.dump(configs, file, indent=4)

def setup(bot):
    bot.add_cog(SetNotifications(bot))
