# OvercastAnalytics
Tool to track played maps and player counts on play.oc.tc.

monitor.py: Gets the data from the server by querying it and extracting the motd, then saving it to a file
flaskapp.py: Defines the routes used in the API with Flask
data_load.py: Defines functions used in flaskapp.py to load the data from the files
