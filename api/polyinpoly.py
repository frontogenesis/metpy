import geopandas
import json
from shapely.geometry import Polygon
from datetime import datetime
from dateutil import tz
from glob import glob

shapefile = geopandas.read_file(glob('../wpc/EXCESSIVERAIN_Day1_latest/*.shp')[0])
states = geopandas.read_file('gis/states/states.shp')
states.set_index('STATE_ABBR', inplace=True)
south_carolina = states.loc['SC']['geometry']
florida = states.loc['FL']['geometry']
louisiana = states.loc['LA']['geometry']
north_carolina = states.loc['NC']['geometry']

# Place data into a Python dictionary
data = {
    "wpc": {
        "excessive_rain_day1": {
            "fl": str((shapefile.intersects(florida)).iloc[0]),
            "sc": str((shapefile.intersects(south_carolina)).iloc[0]),
            "tx": str((shapefile.intersects(louisiana)).iloc[0]),
            "nc": str((shapefile.intersects(north_carolina)).iloc[0])
        }
    }
}