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
    async def set_notifications(self, interaction: discord.Interaction,
                                group: discord.Role, after: int, message: str):
        """
        Set notification settings for a server.
        :param interaction: (Provided by discord)
        :param group: Discord role that will be mentioned
        :param after: Seconds of gametime after which notifications should be sent
        """
        with open(self.config, "r") as file:
            configs = json.load(file)

        configs[interaction.guild_id] = {
            "group": group.id,
            "after": after,
            "channel": interaction.channel.id,
            "message": message
        }

        with open(self.config, "w") as file:
            json.dump(configs, file, indent=4)

        await interaction.response.send_message(
            f"Set notification settings for **{interaction.guild.name}**")


def setup(bot):
    bot.add_cog(SetNotifications(bot))
