import discord
from discord.ext import commands, tasks
import requests
import pathlib
import json
from cogs.current_map import format_seconds  # noqa


class CheckForNotify(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = pathlib.Path("config")
        self.config.touch()
        self.configs = {}
        self.load_config()
        self.check_for_notify.start()
        self.is_notified = dict.fromkeys(self.configs.keys(), False)
        self.tracking_changes = dict.fromkeys(self.configs.keys(), False)

    def cog_unload(self):
        self.check_for_notify.cancel()

    def load_config(self):
        with open(self.config, "r") as file:
            self.configs = json.load(file)

    @discord.slash_command()
    async def reload(self, interaction: discord.Interaction):
        self.load_config()
        await interaction.response.send_message("Reloaded config")

    @tasks.loop(seconds=20)
    async def check_for_notify(self):
        api_response = requests.get(
            "https://quanteey.xyz/Overcast%20Community/current_map/")
        if api_response.status_code == 200:
            current_map = api_response.json()["current_map"]
            is_event = api_response.json()["event"]
            game_time = api_response.json()["game_time"]
            if not is_event:
                for key, value in self.configs.items():
                    if (not self.is_notified[key]
                            and game_time >= self.configs[key]["after"]):
                        self.is_notified[key] = True
                        self.tracking_changes[key] = current_map
                        await self.bot.get_guild(int(key)).get_channel(
                            int(self.configs[key]["channel"])
                        ).send(
                            f"{self.bot.get_guild(int(key)).get_role(int(self.configs[key]['group'])).mention}"
                            f" {self.configs[key]['message']}"
                            f"\n(Game time: **{format_seconds(game_time)}**, Map: **{current_map}**)"
                        )
            for key, value in self.is_notified.items():
                if value and self.tracking_changes[key] != current_map:
                    await self.bot.get_guild(int(key)).get_channel(
                        int(self.configs[key]["channel"])
                    ).send(f"Game ended. The new map is: **{current_map}**.\n")
                    self.is_notified[key] = False
                    self.tracking_changes[key] = False
        else:
            print(f"Unable to get current map - {api_response.status_code}")

    @check_for_notify.before_loop
    async def before_loop_start(self):
        await self.bot.wait_until_ready()
        print("CheckForNotify started!")


def setup(bot):
    bot.add_cog(CheckForNotify(bot))
