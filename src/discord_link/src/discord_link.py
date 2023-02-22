"""
While the general project is made with multiserver support in mind,
this script is specifically made to get the current map from OCC,
even if the main menthod fails (due to an ongoing event.)
"""

import os
import discord
import dotenv
import pathlib

VERSION = "1.0.1"

# Env setup
dotenv.load_dotenv()
TOKEN = str(os.getenv("TOKEN"))
GUILD = int(os.getenv("GUILD"))
TEST_CHANNEL = int(os.getenv("TEST_CHANNEL"))

backup_save = pathlib.Path("../../../save/Overcast Community/backup_current_map.txt")

# Bot setup
intents = discord.Intents.default()
# This seems invalid, but it is taken straight from the docs, and it works.
intents.message_content = True
bot = discord.Bot(intents=intents)

# Load extensions
bot.load_extension("cogs.status")


# Events
@bot.event
async def on_ready():
    print("Ready!")
    await bot.get_guild(GUILD).get_channel(TEST_CHANNEL).send(
        "[STARTUP] QuanteeyAPI Overcast link in UP"
    )
    # Make sure backup savefiles exist
    pathlib.Path("../../../save/Overcast Community").mkdir(parents=True, exist_ok=True)
    backup_save.touch()


@bot.event
async def on_message(message: discord.Message):
    if message.channel.name == "cloudy3-match-status":
        content = message.content.split("`")
        map_ = content[1].strip()
        # Write map to the backup save file
        with open(backup_save, "w") as file:
            file.write(map_)


bot.run(TOKEN)
