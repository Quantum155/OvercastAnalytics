import mcstatus
from time import sleep
import datetime
import os
import pathlib



class Match:
    """
    Basic class for storing all data related to a recently played map.
    """
    def __init__(self, start_date: datetime.datetime, playtime, name, start_players, end_players):
        self.start_date = start_date
        self.playtime = playtime
        self.name = name
        self.start_players = start_players
        self.end_players = end_players

    def get_end_date(self):
        return self.start_date + datetime.timedelta(seconds=self.playtime)

    def get_player_change(self):
        return self.start_players - self.end_players



class Map:
    """
    Class to store data related to a map (Average times etc)
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
            print(f"Calculating player_changes for map {self.map_name}: {self._player_changes}")
            self.average_player_change = sum(self._player_changes) / len(self._player_changes)
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
        self._start_time = datetime.datetime.now()  # This will store the time the last map started.
        self._current_playtime = 0
        self._starting_players = 0
        self._query_cooldown = 0

        self._pending_map = None
        self._is_pending = False

        self._server = mcstatus.JavaServer(address)

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
            status = self._server.status()
            motd = status.description
            active_map_name = motd.splitlines()[1][6:-4]  # Get the map name out from OCC's MOTD

            # Check if the current map is different from the one we got last query
            if self._prev_map != active_map_name:
                if self._verbose: print(f"New map detected. {self._prev_map} >> {active_map_name}")

                # Create the Match object, and print some data if verbose
                self._pending_map = Match(self._start_time, self._current_playtime*self._query_time,
                                          self._prev_map, self._starting_players,
                                          status.players.online)
                self._is_pending = True

                if self._verbose:
                    print(f"------- Finished map -------\n > {self._prev_map} <")
                    print(f"Start time: {str(self._start_time)}")
                    print(f"Playtime: {self._current_playtime * self._query_time} seconds.")
                    print(f"Players at end: {status.players.online} \
                            [{(self._starting_players - status.players.online):+g}]")
                    print(f"---------------------------------\n")


                # Reset the match-tracking variables
                self._prev_map = active_map_name
                self._starting_players = status.players.online
                self._current_playtime = 0
            else:
                # Add one to the current playtime. Time will be obtained by multiplying this with the query time
                if self._verbose: print("No map change detected.")
                self._current_playtime += 1

    def get_pending(self):
        if self._is_pending:
            self._is_pending = False
            return self._pending_map
        else:
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
        self._verbose = verbose

        # Make sure files exists
        pathlib.Path(f"save/{server_name}").mkdir(parents=True, exist_ok=True)
        self._history_file.touch()
        self._map_data.touch()


    def write_data(self, match):
        """
        :param match: The Match object to write
        """
        if match is None:
            pass
        else:
            # Writing map history
            if self._verbose: print(f"Starting the save - Map History")
            with open(self._history_file, "a") as file:
                name = match.name
                stime = str(match.start_date)
                ptime = match.playtime
                splayers = match.start_players
                pchange = match.get_player_change()
                file.write(f"{name} | {stime} | {ptime} | {splayers} | {pchange}\n")

            # Writing map data
            if self._verbose: print(f"Staring the save - Map Data")
            with open(self._map_data, "r") as file:
                data = file.read()

            new_data = ""
            is_written = False
            for line in data.splitlines():
                split = line.split(" | ")
                mapname = split[0]
                playcount = int(split[1])
                if mapname == match.name:
                    is_written = True
                    new_data += f"{mapname} | {playcount+1}\n"
                else:
                    new_data += f"{mapname} | {playcount}\n"
            if not is_written:
                new_data += f"{match.name} | 1\n"


            with open(self._map_data, "w") as file:
                file.write(new_data)

            if self._verbose: print("Write finished.")


class DataAnalyzer:
    """
    Class for analyzing the map_history data for one tracked server, and then "caching" it in map_average_cache.
    """
    def __init__(self, server_save_name, analyze_cooldown=86400):
        """
        :param server_save_name The name of the folder the server data is saved to (save/<name>)
        :param analyze_cooldown: Run caching every x seconds
        """
        self._server_save_name = server_save_name
        self._analyze_cooldown = analyze_cooldown
        self._cooldown = 86400

        self._map_history = pathlib.Path(f"save/{self._server_save_name}/map_history")
        self._save_file = pathlib.Path(f"save/{self._server_save_name}/map_average_cache")

        self._maps = []  # This list will store the Match objects that will be returned after reading the file

        # Make sure files exist
        pathlib.Path(f"save/{self._server_save_name}").mkdir(parents=True, exist_ok=True)
        self._map_history.touch()
        self._save_file.touch()

    def tick(self):
        if self._cooldown > 0:
            self._cooldown -= 1
        else:
            # Calculate average datas for each map (Average playtime, playercount, playercount change)
            # Read each map line by line from map_history, construct a list of Match objects
            # Then calculate the averages and write them to a file.
            # If we run this script for 1 year then the map_history will only be around 1 MB,
            # so we don't have to worry about loading too much stuff into memory.
            self._cooldown = self._analyze_cooldown

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




if __name__ == "__main__":
    # Example run

    occmonitor = ServerMonitor("play.oc.tc", verbose=True)
    occwriter = DataWriter("occ", verbose=True)
    occanalyzer = DataAnalyzer("occ")

    while True:
        occmonitor.tick()
        match = occmonitor.get_pending()
        occwriter.write_data(match)
        occanalyzer.tick()
        sleep(1)
