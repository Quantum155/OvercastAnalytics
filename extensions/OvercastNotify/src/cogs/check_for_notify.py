import discord
from discord.ext import commands
import requests
import pathlib
import json


class CheckForNotify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = pathlib.Path("config")
        self.config.touch()


def setup(bot):
    bot.add_cog(CheckForNotify(bot))
