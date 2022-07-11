import mcstatus
from time import sleep
import datetime
import os



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

    :param address Address to query
    :type str
    :param query_time Time between each query in seconds. (default is 30)
    :type int
    :param verbose Should the server monitor print out debug / map information to stdout
    :type bool

    Methods:
    tick()
        Should be ran once every second. It queries the server, and if a new map is found, adds a Match object to the
        queue
    """
    def __init__(self, address, query_time=30, verbose=False):
        self._address = address
        self._query_time = query_time
        self._verbose = verbose

        self._prev_map = "Initializing"
        self._start_time = datetime.datetime.now()  # This will store the time the last map started.
        self._current_playtime = 0
        self._starting_players = 0
        self._query_cooldown = 0

        self._queue = []  # List for storing maps

        self._server = mcstatus.JavaServer(address)

    def tick(self):
        # Check if the query cooldown expired, if yes reset it and query the server
        if self._query_cooldown < 0:
            self._query_cooldown -= 1
        else:
            # Reset cooldown
            self._query_cooldown = self._query_time

            # Query the server
            status = server.status()
            motd = status.description
            active_map_name = motd.splitlines()[1][6:-4]  # Get the map name out from OCC's MOTD

            # Check if the current map is different from the one we got last query
            if self._prev_map != active_map_name:
                if self._verbose: print(f"New map detected. {self._prev_map} >> {active_map_name}")

                # Create the Match object, and print some data if verbose
                self._queue.append(Match(self._start_time, self._current_playtime, active_map_name,
                                         self._starting_players, status.players.online))
                if self._verbose:
                    print(f"------- Last finished map -------\n > {active_map_name} <")
                    print(f"Start time: {str(self._start_time)}")
                    print(f"Playtime: {self._current_playtime * self._query_time}")
                    print(f"Players at end: {status.players.online} \
                            [{(self._starting_players - status.players.online):+g}]")

                # Reset the match-tracking variables
                self._prev_map = active_map_name
                self._starting_players = status.players.online
                self._current_playtime = 0
            else:
                # Add one to the current playtime. Time will be obtained by multiplying this with the query time
                self._current_playtime += 1



# Previous code for reference, rewrite not complete.
"""
while True:

    status = server.status()
    motd = status.description

    active_map = motd.splitlines()[1][6:-4]

    if prev_map != active_map:
        print("New map detected.")

        with open("data.txt", "a") as file:
            towrite = f"{prev_map} | {playtime * QUERY_TIME} | {status.players.online} | {start_players}\n"
            print("Saving data " + towrite)
            file.write(towrite)

        prev_map = active_map
        start_players = status.players.online
        playtime = 0
    else:
        playtime += 1

    playtime_hr = datetime.timedelta(seconds=QUERY_TIME*playtime)

    print(f"Current map: {active_map} | Playtime: {playtime_hr} | Players {status.players.online} [Players at start: {start_players}, {status.players.online - start_players} change]")
    sleep(QUERY_TIME)
    os.system('cls' if os.name == 'nt' else 'clear')
"""