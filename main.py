import mcstatus
from time import sleep
import datetime
import os

QUERY_TIME = 30

server = mcstatus.JavaServer("occanalytics.oc.tc")

prev_map = "INIT"
playtime = 0
start_players = 0

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
