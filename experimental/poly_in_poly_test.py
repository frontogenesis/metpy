import geopandas
import json
from shapely.geometry import Polygon
from datetime import datetime
from dateutil import tz

shapefile = geopandas.read_file('wpc/EXCESSIVERAIN_Day2_latest/98e1809.shp')
states = geopandas.read_file('gis/states/states.shp')
states.set_index('STATE_ABBR', inplace=True)
south_carolina = states.loc['SC']['geometry']
florida = states.loc['FL']['geometry']

# Place data into a Python dictionary
data_dict = {
    "wpc": {
        "excessive_rain_day1": {
            "fl": str((shapefile.intersects(florida)).iloc[0]),
            "sc": str((shapefile.intersects(south_carolina)).iloc[0])
        }
    }
}

# Convert to JSON string
data_json = json.dumps(data_dict)