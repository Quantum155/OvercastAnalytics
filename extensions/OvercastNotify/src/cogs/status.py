import discord
from discord.ext import commands
import requests


class Status(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def online(self, interaction: discord.Interaction):
        api_response = requests.get("https://quanteey.xyz/")
        version = api_response.json()["api_version"]
        monitor_version = api_response.json()["monitor_version"]
        if api_response.status_code == 200:
            await interaction.response.send_message(f"Quanteey API is online"
                                                    f" (**{int(api_response.elapsed.total_seconds()*1000)}ms**)\n"
                                                    f"Quanteey API version: **{version}**\n"
                                                    f"Monitor version: **{monitor_version}**")
        else:
            await interaction.response.send_message(f"Quanteey API is not online / failed:"
                                                    f" error **{api_response.status_code}**")


def setup(bot):
    bot.add_cog(Status(bot))
