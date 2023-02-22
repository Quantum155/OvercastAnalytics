import discord
from discord.ext import commands
import requests
from cogs.current_map import format_seconds  # noqa


class MapData(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @discord.slash_command()
    async def get_map_data(self, interaction: discord.Interaction, map_name: str):
        api_response = requests.get(
            f"https://quanteey.xyz/Overcast%20Community/maps/{map_name}"
        )
        if api_response.status_code == 200:
            found_in_cache = api_response.json()["found_in_cache"]
            playcount = api_response.json()["playcount"]
            map_avg_playtime = int(api_response.json()["map_avg_playtime"])
            map_avg_playercount_change = api_response.json()[
                "map_avg_playercount_change"
            ]
            await interaction.response.send_message(
                f"Data for map: **{map_name}**\n"
                f"Is cached: **{found_in_cache}**\n"
                f"Times played: **{playcount}**\n"
                f"Average playtime: **{format_seconds(map_avg_playtime)}**\n"
                f"Average playercount change: **{map_avg_playercount_change:.2f}**"
            )
        elif api_response.status_code == 404:
            await interaction.response.send_message(
                f"Requested map is not found: **{map_name}**"
            )
        else:
            await interaction.response.send_message(
                f"Quanteey API is not online / failed:"
                f" error **{api_response.status_code}**"
            )


def setup(bot):
    bot.add_cog(MapData(bot))
