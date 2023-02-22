import flask
import pathlib
from src.monitor.monitor import get_monitor_version
from data_load import *

DEVELOPMENT = False
API_VERSION = "3.0.5"
MONITOR_SERVERS = [
    "Overcast Community"
]  # Folders inside ../../save/ from where the API can serve data from.


def has_access(server):
    if server in MONITOR_SERVERS:
        return True
    return False


app = flask.Flask(__name__)


@app.route("/", methods=["GET"])
def index():
    """
    This gets information about the API and Monitor.
    """
    return flask.jsonify({
        "api_version": API_VERSION,
        "monitor_version": get_monitor_version(),
        "monitored_server_count": len(MONITOR_SERVERS),
        "monitored_servers": MONITOR_SERVERS
    })


@app.route("/<string:server_name>/", methods=["GET"])
def server_data(server_name):
    """
    Return information about a tracked server.
    :param server_name: Name of the server
    """
    # Make sure accessing that data is allowed
    if not has_access(server_name):
        return flask.jsonify("Requested server not found or forbidden"), 403

    directory = pathlib.Path(f"../../save/{server_name}")

    if directory.is_dir():
        monitoring_since, last_cache, maps_tracked = load_server_data(
            directory)
        player_sample = load_players(directory)
        # Return response
        return flask.jsonify({
            "name": server_name,
            "monitoring_since": monitoring_since,
            "last_cache_update": last_cache,
            "maps_tracked": maps_tracked,
            "player_sample": player_sample
        })
    return flask.jsonify("Requested server not found"), 404


@app.route("/<string:server_name>/current_map/")
def current_map(server_name):
    """
    Returns the currently playing map
    :param server_name: Name of the server
    """
    if not has_access(server_name):
        return flask.jsonify("Requested server not found or forbidden"), 403

    directory = pathlib.Path(f"../../save/{server_name}")

    if directory.is_dir():
        active_map = load_active_map(directory)
        event = False
        if active_map == "SYS_EVENT":
            event = True
        if server_name == "Overcast Community":
            #  Always use the more reliable cloudy source (that comes from Cloudy)
            #  This is a terrible implementation, but it works.
            #  (Also, it's hard to avoid it without a major refactor)
            active_map = load_occ_backup_data()
        game_time = load_game_time(directory)
        return flask.jsonify({
            "current_map": active_map,
            "game_time": game_time,
            "event": event
        })
    return flask.jsonify("Requested server not found"), 404


@app.route("/<string:server_name>/maps/<string:map_name>/", methods=["GET"])
def map_data(server_name, map_name):
    """
    Returns data about a specific map on a server
    :param server_name: Name of the server
    :param map_name: Name of the map
    """
    if not has_access(server_name):
        return flask.jsonify("Requested server not found or forbidden"), 403

    directory = pathlib.Path(f"../../save/{server_name}")

    if directory.is_dir():
        # Load data for map
        is_found, cached_data_found, map_playcount, map_avg_playtime, map_avg_playercount_change = load_map_data(
            directory, map_name)

        if not is_found:
            return flask.jsonify("Requested map not found"), 404
        return flask.jsonify({
            "server_name":
            server_name,
            "map_name":
            map_name,
            "found_in_cache":
            cached_data_found,
            "playcount":
            map_playcount,
            "map_avg_playtime":
            map_avg_playtime,
            "map_avg_playercount_change":
            map_avg_playercount_change
        })
    return flask.jsonify("Requested server not found"), 404


if __name__ == '__main__':
    if DEVELOPMENT:
        app.run(host="127.0.0.1", port=7000)
    else:
        app.run(host="0.0.0.0", port=7000)  # noqa