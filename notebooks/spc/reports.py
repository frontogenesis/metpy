import pandas as pd
import cartopy.crs as ccrs
from matplotlib.lines import Line2D

def plot_spc_reports(ax, day='yesterday'):
    '''Pass in a single axes and returns SPC reports with a legend'''
    
    spc_wind, spc_tornado, spc_hail = get_spc_csv(day)
    
    ax.scatter(spc_wind.Lon, spc_wind.Lat, transform=ccrs.PlateCarree(), marker='o', s=200, c='blue', zorder=3)
    ax.scatter(spc_tornado.Lon, spc_tornado.Lat, transform=ccrs.PlateCarree(), marker='v', s=800, c='red', zorder=3)
    ax.scatter(spc_hail.Lon, spc_hail.Lat, transform=ccrs.PlateCarree(), 
               marker='s', s=200, c='green', zorder=3)
    
    legend_elements = [Line2D([0], [0], marker='v', color='w', label='Tornado',
                          markerfacecolor='red', markersize=30),
                   Line2D([0], [0], marker='o', color='w', label='Wind',
                          markerfacecolor='blue', markersize=30),
                   Line2D([0], [0], marker='s', color='w', label='Hail',
                          markerfacecolor='green', markersize=30)]

    ax.legend(handles=legend_elements, loc='lower left', fontsize=32)
    
    return ax

def get_spc_csv(day):
    '''Pass in today or yesterday as the day parameter and it returns the SPC reports'''
    spc_wind = pd.read_csv(f'https://www.spc.noaa.gov/climo/reports/{day}_wind.csv')
    spc_tornado = pd.read_csv(f'https://www.spc.noaa.gov/climo/reports/{day}_torn.csv')
    spc_hail = pd.read_csv(f'https://www.spc.noaa.gov/climo/reports/{day}_hail.csv')
    
    return spc_wind, spc_tornado, spc_hail