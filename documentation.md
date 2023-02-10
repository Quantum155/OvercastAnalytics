# API documentation

> Things marked as [FUTURE] will be implemented in the future

### Get API status
```
[GET] /
---
Response {
    "api_version": str,
    "monitor_version": str,
    "monitored_server_count": int,
    "monitored_servers": list[str]
}
```

### Get general info of a monitored server
```
"parameter" <servername>: str
[GET] /<servername>/
---
Response {
    "name": str,  # Same as original parameter
    "monitoring_since": str,
    "last_cache_update": str,
    "maps_tracked": int,
    "player_sample": list[str]
}
```

### Get currently playing map
```
"parameter" <servername>: str
[GET] /<servername>/current_map/
---
Response {
    "current_map": str,
    "playtime": int
}
```

### Get data about a specific map
```
"parameter" <servername>: str
"paremeter" <mapname>: str
[GET] /<servername>/current_map/<mapname>/
---
Response {
    "server_name": str, # Same as original parameter
    "map_name": str,
    "found_in_cache": bool,
    "playcount": int,
    "map_avg_playtime": int,
    "map_avg_playercount_change": int
}
```