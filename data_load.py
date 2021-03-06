def load_map_data(directory, map_name):
    is_found = False
    with open((directory / "map_data"), "r") as file:
        data = file.read()

        map_playcount = 0
        for line in data.splitlines():
            split = line.split(" | ")
            mapname_to_check = split[0]
            playcount = int(split[1])

            if mapname_to_check == map_name:
                # The requested map exists
                is_found = True
                map_playcount = playcount
                break

    # Load cached data, if any
    cached_data_found = False
    with open((directory / "map_average_cache"), "r") as file:
        data = file.read()

        map_avg_playtime = 0
        map_avg_playercount_change = 0
        for line in data.splitlines():
            split = line.split(" | ")
            mapname = split[0]
            playtime = float(split[1])
            pcount_change = float(split[2])

            if mapname_to_check == mapname:
                # The requested map exists
                cached_data_found = True
                map_avg_playtime = playtime
                map_avg_playercount_change = pcount_change
                break

    return is_found, cached_data_found, map_playcount, map_avg_playtime, map_avg_playercount_change


def load_server_data(directory):
    # Read files
    with open((directory / "first_write"), "r") as file:
        monitoring_since = file.read()
    with open((directory / "last_cache_time"), "r") as file:
        last_cache = file.read()
    # Count number of maps in file
    invalid = 0
    with open((directory / "map_data"), 'r') as fp:
        for count, line in enumerate(fp):
            if line.startswith("SYS_"): invalid += 1
    maps_tracked = count + 1 - invalid

    return monitoring_since, last_cache, maps_tracked


def load_active_map(directory):
    with open((directory / "active_map"), "r") as file:
        return file.read()
