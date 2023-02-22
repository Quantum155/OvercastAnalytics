import mcstatus
from time import sleep
import datetime
import pathlib

MONITOR_VERSION = "2.0.4"


def get_monitor_version():
    return MONITOR_VERSION


class TimedData:
    """
    Basic class for storing everything that needs to be saved periodically, rather than at the end of the game
    """

    def __init__(
        self, online_players: list, is_complete: False, playercount: int, game_time: int
    ):
        self.playercount = playercount
        self.online_players = online_players
        self._is_complete = is_complete  # Is the data complete (as a result of a query instead of a status check)
        self.game_time = game_time

    def get_player_names(self):
        player_names = []
        for player in self.online_players:
            player_names.append(player.name)
        return player_names


class Match:
    """
    Basic class for storing all data related to a recently played map.
    """

    def __init__(
        self,
        start_date: datetime.datetime,
        playtime,
        name,
        start_players,
        end_players,
        is_event: bool,
    ):
        self.start_date = start_date
        self.playtime = playtime
        self.name = name
        self.start_players = start_players
        self.end_players = end_players
        self.is_event = is_event

    def get_end_date(self):
        return self.start_date + datetime.timedelta(seconds=self.playtime)

    def get_player_change(self):
        return self.end_players - self.start_players


class Map:
    """
    Class to store data related to a map (Average times etc.)
    Also has functions to calculate the data.
    """

    def __init__(self, map_name, average_playtime=None, average_player_change=None):
        self.map_name = map_name
        self.average_playtime = average_playtime
        self.average_player_change = average_player_change

        self._playtimes = []
        self._player_changes = []

    def calculate_average_playtimes(self):
        if len(self._playtimes) > 0:
            self.average_playtime = sum(self._playtimes) / len(self._playtimes)
        else:
            pass

    def calculate_average_player_changes(self):
        if len(self._player_changes) > 0:
            self.average_player_change = sum(self._player_changes) / len(
                self._player_changes
            )
        else:
            pass

    def add_playtime(self, time):
        self._playtimes.append(time)

    def add_player_change(self, change):
        self._player_changes.append(change)


class ServerMonitor:
    """
    Class for monitoring one server.

    Methods:
    tick()
        Should be ran once every second. It queries the server, and if a new map is found, it sets the pending_map to
        the Match object
    get_pending_map()
        returns the pending map
    """

    def __init__(self, address, query_time=30, verbose=False):
        """
        :param address Address to query
        :param query_time Time between each query in seconds. (default is 30)
        :param verbose Should the server monitor print out debug / map information to stdout
        """
        self._address = address
        self._query_time = query_time
        self._verbose = verbose

        self._prev_map = "SYS_INIT"
        self._start_time = (
            datetime.datetime.now()
        )  # This will store the time the last map started.
        self._current_playtime = 0
        self._starting_players = 0
        self._query_cooldown = 0

        self._pending_map = None
        self._is_pending = False

        self._server = mcstatus.JavaServer(address)

        self._online_players = []

        self._timed_data = None
        self._is_timed_data_pending = False

        self._is_event = False

    def tick(self):
        # Check if the query cooldown expired, if yes reset it and query the server
        if self._query_cooldown > 0:
            self._query_cooldown -= 1
        else:
            if self._verbose:
                print(f"Querying server. [{self._current_playtime}]")

            # Reset cooldown
            self._query_cooldown = self._query_time

            # Query the server
            try:
                status = self._server.status()
                motd = status.description
                players = status.players.online
                self._online_players = status.players.sample
                active_map_name = motd.splitlines()[1][
                    6:-4
                ]  # Get the map name out from OCC's MOTD
            except (
                Exception  # skipcq: PYL-W0703 - We want to catch every exception
            ) as ex:
                print(f"[ERROR] Unable to query server: {ex}")
                active_map_name = "SYS_QUERYERROR"
                players = 0
                self._online_players = []

            # Create timed objects
            self._timed_data = TimedData(
                self._online_players,
                is_complete=False,
                playercount=players,
                game_time=self._current_playtime * self._query_time,
            )
            self._is_timed_data_pending = True

            # Check if the current map is different from the one we got last query
            if self._prev_map != active_map_name:
                if "§" in active_map_name:
                    self._is_event = True
                if self._verbose:
                    print(f"New map detected. {self._prev_map} >> {active_map_name}")

                # Create the Match object, and print some data if verbose
                self._pending_map = Match(
                    self._start_time,
                    self._current_playtime * self._query_time,
                    self._prev_map,
                    self._starting_players,
                    players,
                    self._is_event,
                )
                self._is_pending = True

                if self._verbose:
                    print(f"------- Finished map -------\n > {self._prev_map} <")
                    print(f"Start time: {str(self._start_time)}")
                    print(
                        f"Playtime: {self._current_playtime * self._query_time} seconds."
                    )
                    print(
                        f"Players at end: {players} \
                            [{players - self._starting_players:+g}]"
                    )
                    print(f"Is event: {self._is_event}")
                    print("---------------------------------\n")

                # Reset the match-tracking variables
                self._prev_map = active_map_name
                self._starting_players = players
                self._current_playtime = 0
            else:
                # Add one to the current playtime. Time will be obtained by multiplying this with the query time
                if self._verbose:
                    print("No map change detected.")
                self._current_playtime += 1

    def get_pending(self):
        if self._is_pending:
            self._is_pending = False
            return self._pending_map
        return None

    def get_active(self):
        return self._prev_map

    def get_timed(self):
        if self._is_timed_data_pending:
            self._is_timed_data_pending = False
            return self._timed_data
        return None


class DataWriter:
    """
    Class for writing data to the disk. Handles writing the data for one server.
    """

    def __init__(self, server_name, verbose=False):
        """
        :param server_name Name of the server. Used in naming the folder.
        :param verbose Display debug information (Default is False)
        """
        self._history_file = pathlib.Path(f"save/{server_name}/map_history")
        self._map_data = pathlib.Path(f"save/{server_name}/map_data")
        self._active_map = pathlib.Path(f"save/{server_name}/active_map")
        self._game_time = pathlib.Path(f"save/{server_name}/game_time")
        self._first_write = pathlib.Path(f"save/{server_name}/first_write")
        self._online_players = pathlib.Path(f"save/{server_name}/online")
        self._misc_data = pathlib.Path(f"save/{server_name}/misc")
        self._player_history = pathlib.Path(f"save/{server_name}/player_history")
        self._verbose = verbose

        # Make sure files exists
        pathlib.Path(f"save/{server_name}").mkdir(parents=True, exist_ok=True)
        self._history_file.touch()
        self._map_data.touch()
        self._active_map.touch()
        self._game_time.touch()
        self._misc_data.touch()
        self._online_players.touch()
        self._player_history.touch()

        # Check if first_write exists, if yes then pass, if not then create it.
        if self._first_write.is_file():
            pass
        else:
            with open(self._first_write, "w") as file:
                file.write(str(datetime.datetime.now()))

    def write_data(self, _match: Match, active_map: str):
        """
        :param _match: The Match object to write
        :param active_map: The name of the active map
        """
        if _match is None:
            pass
        else:
            if _match.is_event:
                with open(self._active_map, "w") as file:
                    file.write("SYS_EVENT")

                with open(self._history_file, "a") as file:
                    name = "SYS_EVENT"
                    stime = str(_match.start_date)
                    ptime = _match.playtime
                    splayers = _match.start_players
                    pchange = _match.get_player_change()
                    file.write(f"{name} | {stime} | {ptime} | {splayers} | {pchange}\n")
            else:
                # Writing map history
                if self._verbose:
                    print("Starting the save - Map History")
                with open(self._history_file, "a") as file:
                    name = _match.name
                    stime = str(_match.start_date)
                    ptime = _match.playtime
                    splayers = _match.start_players
                    pchange = _match.get_player_change()
                    file.write(f"{name} | {stime} | {ptime} | {splayers} | {pchange}\n")

                if self._verbose:
                    print("Starting the save - Active map")
                with open(self._active_map, "w") as file:
                    file.write(active_map)

                # Writing map data
                if self._verbose:
                    print("Staring the save - Map Data")
                with open(self._map_data, "r") as file:
                    data = file.read()

                new_data = ""
                is_written = False
                for line in data.splitlines():
                    split = line.split(" | ")
                    mapname = split[0]
                    playcount = int(split[1])
                    if mapname == _match.name:
                        is_written = True
                        new_data += f"{mapname} | {playcount+1}\n"
                    else:
                        new_data += f"{mapname} | {playcount}\n"
                if not is_written:
                    new_data += f"{_match.name} | 1\n"

                with open(self._map_data, "w") as file:
                    file.write(new_data)

                if self._verbose:
                    print("Write finished.")

    def write_timeds(self, timed: TimedData):
        if timed is None:
            pass
        else:
            if self._verbose:
                print("Writing online players.")
            with open(self._online_players, "w") as file:
                for item in timed.get_player_names():
                    file.write(str(item) + "\n")
            with open(self._player_history, "a") as file:
                file.write(
                    datetime.datetime.now().isoformat()
                    + "|"
                    + str(timed.playercount)
                    + "|"
                )
                for item in timed.get_player_names():
                    file.write(str(item) + "|")
                file.write("\n")
            with open(self._game_time, "w") as file:
                file.write(str(timed.game_time).strip() + "\n")


class DataAnalyzer:
    """
    Class for analyzing the map_history data for one tracked server, and then "caching" it in map_average_cache.
    """

    def __init__(self, server_save_name, analyze_cooldown=43200):
        """
        :param server_save_name The name of the folder the server data is saved to (save/<name>)
        :param analyze_cooldown: Run caching every x seconds
        """
        self._server_save_name = server_save_name
        self._analyze_cooldown = analyze_cooldown
        self._cooldown = 0

        self._map_history = pathlib.Path(f"save/{self._server_save_name}/map_history")
        self._save_file = pathlib.Path(
            f"save/{self._server_save_name}/map_average_cache"
        )
        self._last_cache_save = pathlib.Path(
            f"save/{self._server_save_name}/last_cache_time"
        )

        self._maps = (
            []
        )  # This list will store the Match objects that will be returned after reading the file

        # Make sure files exist
        pathlib.Path(f"save/{self._server_save_name}").mkdir(
            parents=True, exist_ok=True
        )
        self._map_history.touch()
        self._save_file.touch()
        self._last_cache_save.touch()

    def tick(self):
        if self._cooldown > 0:
            self._cooldown -= 1
        else:
            self.analyze_maps()

    def analyze_maps(self):
        # Calculate average datas for each map (Average playtime, playercount, playercount change)
        # Read each map line by line from map_history, construct a list of Match objects
        # Then calculate the averages and write them to a file.
        # If we run this script for 1 year then the map_history will only be around 1 MB,
        # so we don't have to worry about loading too much stuff into memory.
        self._cooldown = self._analyze_cooldown
        print("Starting map average calculations.")
        # Scan the file
        with open(self._map_history, "r") as file:
            for line in file:
                split = line.split(" | ")
                name = split[0]
                playtime = int(split[2])
                change = int(split[4])
                # check if a Map with a matching name exists in self._maps
                found = False
                for map_ in self._maps:
                    if map_.map_name == name:
                        map_.add_playtime(playtime)
                        map_.add_player_change(change)
                        found = True

                if not found:
                    map_to_add = Map(name)
                    map_to_add.add_playtime(playtime)
                    map_to_add.add_player_change(change)
                    self._maps.append(map_to_add)
        # Make the calculations
        for map_ in self._maps:
            map_.calculate_average_playtimes()
            map_.calculate_average_player_changes()
        # Get what to write
        to_write = ""
        for map_ in self._maps:
            name = map_.map_name
            playtime = map_.average_playtime
            player_change = map_.average_player_change
            to_write += f"{name} | {playtime} | {player_change}\n"
        # Write to disk
        with open(self._save_file, "w") as file:
            file.write(to_write)
        print("Calculations completed")
        with open(self._last_cache_save, "w") as file:
            file.write(str(datetime.datetime.now()))


if __name__ == "__main__":
    # Example run
    print(f"Started - Saving to {str(pathlib.Path('save/'))} ")

    occmonitor = ServerMonitor("play.oc.tc", verbose=True, query_time=10)
    occwriter = DataWriter("Overcast Community", verbose=True)
    occanalyzer = DataAnalyzer("Overcast Community")

    while True:
        occmonitor.tick()
        match = occmonitor.get_pending()
        active = occmonitor.get_active()
        timeds = occmonitor.get_timed()
        occwriter.write_data(match, active)
        occwriter.write_timeds(timeds)
        occanalyzer.tick()
        sleep(1)
