import warnings
import gzip
import urllib
import tempfile
from datetime import datetime, timedelta

try:
    import xarray as xr
except:
    warnings.warn('Warning: XArray is not installed in your environment.')
    
try:
    import pygrib
except:
    warnings.warn('Warning: Pygrib is not installed in your environment.')

try:
    from dateutil import tz
except:
    warnings.warn('Warning: Pygrib is not installed in your environment.')


class Data:
    def __init__(self, url):
        self.url = url

    def xr_read_dataset(self):
        '''
        Reads in data over the network, writes it as a temporary file,
        and returns an XArray Dataset
        '''
        response = urllib.request.urlopen(self.url)
        compressed_file = response.read()

        with tempfile.NamedTemporaryFile(suffix='.grib2') as f:
            f.write(gzip.decompress(compressed_file))
            return xr.load_dataset(f.name)
        
    def pygrib_read_dataset(self):
        '''
        Reads in data over the network, writes it as a temporary file,
        and returns a Pygrib Dataset
        '''
        response = urllib.request.urlopen(self.url)
        file = response.read()
    
        with tempfile.NamedTemporaryFile(suffix='.grib2') as f:
            f.write(file)
            ds = pygrib.open(f.name)
            # Reset the grib messages to 0 so you're at beginning of the file
            ds.seek(0)
            return ds

class ValidTime:
    def __init__(self, valid_date, valid_time, timezone='America/New York'):
        self.valid_date = valid_date
        self.valid_time = valid_time
        self.timezone = timezone

    def construct_valid_time(self):
        return str(self.valid_date) + ' ' + str(self.valid_time)

    def roundTime(self, dt=None, roundTo=60):
        """Round a datetime object to any time lapse in seconds
        dt : datetime.datetime object, default now.
        roundTo : Closest number of seconds to round to, default 1 minute.
        Author: Thierry Husson 2012 - Use it as you want but don't blame me.
        """
        if dt == None : dt = datetime.now()
        seconds = (dt.replace(tzinfo=None) - dt.min).seconds
        rounding = (seconds+roundTo/2) // roundTo * roundTo
        return dt + timedelta(0,rounding-seconds,-dt.microsecond) 

    def convert_datetime_pygrib(self):
        """Returns valid local time from a pygrib object"""
        from_zone = tz.gettz('UTC')
        to_zone = tz.gettz(self.timezone)

        pygrib_time = self.construct_valid_time()
        
        # Handle weird issue where a valid time of 00Z is in format
        # YYYYMMDD H
        # All other valid times are in format YYYYMMDDHHMM  
        if pygrib_time.split(' ')[1] == '0': 
            utc_time = datetime.strptime(pygrib_time, '%Y%m%d %H').replace(tzinfo=from_zone)
        else:
            utc_time = datetime.strptime(pygrib_time, '%Y%m%d %H%M').replace(tzinfo=from_zone)
            
        local_time = utc_time.astimezone(to_zone)
        local_time = self.roundTime(local_time)
        date_time = datetime.strftime(local_time, '%a, %b %d, %Y %I:%M %p').lstrip('0').replace(' 0', ' ')
        
        return date_time
