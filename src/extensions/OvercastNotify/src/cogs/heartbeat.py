from discord.ext import tasks, commands
import requests
import dotenv
import os


dotenv.load_dotenv()
TELEMETRY_TOKEN = os.getenv("TELEMETRY_TOKEN")


class Heartbeat(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.heartbeat.start()

    def cog_unload(self):
        self.heartbeat.cancel()

    @tasks.loop(seconds=60)
    async def heartbeat(self):
        requests.get(f"https://cronitor.link/p/{TELEMETRY_TOKEN}/occ-notify")


def setup(bot):
    bot.add_cog(Heartbeat(bot))
