import discord
from discord.ext import commands
import requests
import datetime


def format_seconds(seconds: int) -> str:
    # This is terrible but it works
    time_str = str(datetime.timedelta(seconds=seconds))
    times = time_str.split(":")
    hours = int(times[0])
    minutes = int(times[1])
    seconds = int(times[2])

    if seconds == 0:
        seconds_text = ""
    elif seconds == 1:
        seconds_text = f"{seconds} second"
    else:
        seconds_text = f"{seconds} seconds"

    if minutes == 0:
        minutes_text = ""
    elif minutes == 1:
        minutes_text = f"{minutes} minute"
    else:
        minutes_text = f"{minutes} minutes"

    if hours == 0:
        hours_text = ""
    elif hours == 1:
        hours_text = f"{hours} hour"
    else:
        hours_text = f"{hours} hours"

    return f"{hours_text} {minutes_text} {seconds_text}".strip()


class CurrentMap(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def current_map(self, interaction: discord.Interaction):
        api_response = requests.get(
            "https://quanteey.xyz/Overcast%20Community/current_map/")
        if api_response.status_code == 200:
            current_map = api_response.json()["current_map"]
            is_event = api_response.json()["event"]
            if is_event:
                is_event = "Yes"
            else:
                is_event = "No"
            game_time = api_response.json()["game_time"]
            await interaction.response.send_message(
                f"Current map: **{current_map}**\n"
                f"Event: **{is_event}**\n"
                f"Game time: **{format_seconds(game_time)}**")
        else:
            await interaction.response.send_message(
                f"Quanteey API is not online / failed:"
                f" error {api_response.status_code}")


def setup(bot):
    bot.add_cog(CurrentMap(bot))
