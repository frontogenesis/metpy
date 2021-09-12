import warnings

try:
    import matplotlib.pyplot as plt
except:
    warnings.warn('Warning: Matplotlib is not installed in your environment.')
    
try:
    import cartopy.feature as cfeature
    from cartopy import crs as ccrs
except:
    warnings.warn('Warning: Cartopy is not installed in your environment.')
    
try:
    from metpy.plots import USCOUNTIES
except:
    warnings.warn('Warning: MetPy is not installed in your environment.')

class Map:
    
    def __init__(self, region, proj=ccrs.PlateCarree()):
        '''
        Builds a map from a pre-defined set of regions.
        See the areas dict in the make_map method for these areas.
        '''
        self.region = region.lower()
        self.fig = plt.figure(figsize=(1280/72, 720/72))
        self.ax = self.fig.add_axes([0, 0, 1, 1], projection=proj)
        self.ax.add_feature(cfeature.OCEAN.with_scale('50m'), color='lightgray')
        self.hi_res_states = self.ax.add_feature(cfeature.STATES.with_scale('10m'), linewidth=1.5, zorder=5)
        self.ax.set_adjustable('datalim')
        self.ax.spines['geo'].set_visible(False)
        
    def make_map(self):    
        areas = {
            'mid_atlantic': [-79.0, -71.0, 38, 41.5],
            'southeast': [-91, -77, 23.5, 38.5],
            'florida': [-86.0, -81.0, 23.3, 33.0],
            'florida_panhandle': [-87.5, -83.5, 28.7, 32.2],
            'south_carolina': [-82, -79, 31.2, 36.3],
            'tropical_atlantic': [-100, -10, 5, 42]
        }.get(self.region, [-130, -65, 22, 48])
        
        self.ax.set_extent(areas)
        
        return self.fig, self.ax
    
    def add_title(self, title):
        '''Add title to map axes'''
        self.ax.set_title(title, loc='left', ha='left', va='top', 
                          fontsize=48, color='white', fontweight='bold', 
                          fontname='Arial', y=0.95, x=0.01, zorder=10,
                          bbox=dict(facecolor='navy', alpha=1.0, edgecolor='none'))
    
    def add_counties(self):
        '''Add U.S. counties to map axes'''
        self.ax.add_feature(USCOUNTIES.with_scale('20m'), edgecolor='lightgray', 
                            linewidth=0.75, zorder=4)
        
    def add_latlon_lines(self):
        '''Add latitude and longitude gridlines to the map axes'''
        gl = self.ax.gridlines(crs=ccrs.PlateCarree(), draw_labels=True,
             linewidth=2, color='gray', alpha=0.5, linestyle='--')
        gl.top_labels = False
        gl.left_labels = False
        gl.xlabel_style = {'size': 15, 'color': 'gray'}
        gl.ylabel_style = {'size': 15, 'color': 'gray'}
        
    def remove_international_states(self):
        '''
        Removes state boundary from international counties, like Mexican states 
        or Cuban provinces. This method is ideally called when building a wide view
        of the Tropical Atlantic Basin.
        '''
        self.hi_res_states.set_visible(False)
        self.ax.add_feature(cfeature.STATES.with_scale('50m'), linewidth=2.0, zorder=5)
        self.ax.add_feature(cfeature.COASTLINE.with_scale('10m'))