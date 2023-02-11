# OvercastAnalytics
[![DeepSource](https://deepsource.io/gh/Quantum155/OvercastAnalytics.svg/?label=active+issues&show_trend=true&token=zfwolrih2FPA5BGLTWI4W-Fo)](https://deepsource.io/gh/Quantum155/OvercastAnalytics/?ref=repository-badge)

Tool to track played maps and player counts on play.oc.tc.

monitor.py: Gets the data from the server by querying it and extracting the motd, then saving it to a file

flaskapp.py: Defines the routes used in the API with Flask

data_load.py: Defines functions used in flaskapp.py to load the data from the files

overcast-map-link.py: A pycord discord bot to read map data from Cloudy even if the query method fails
