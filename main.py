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



if __name__ == "__main__":
    # Example run

    occmonitor = ServerMonitor("play.oc.tc", verbose=True)
    occwriter = DataWriter("occ", verbose=True)

    while True:
        occmonitor.tick()
        match = occmonitor.get_pending()
        occwriter.write_data(match)
        sleep(1)
