import os
import discord
import dotenv

VERSION = "dev0"

# Env setup
dotenv.load_dotenv()
TOKEN = str(os.getenv("TOKEN"))

# Bot setup
intents = discord.Intents.default()
bot = discord.Bot(intents=intents)

# Load extensions
bot.load_extension("cogs.status")
bot.load_extension("cogs.current_map")
bot.load_extension("cogs.check_for_notify")
bot.load_extension("cogs.set_notifications")
bot.load_extension("cogs.get_map_data")


# Events
@bot.event
async def on_ready():
    print("Ready!")


bot.run(TOKEN)
