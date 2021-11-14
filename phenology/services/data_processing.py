import ee
from django.core.exceptions import BadRequest
from .constants import dataset_names, feature_list
from .speckle_filters import dbToPower
# from .conversion import geojson_to_ee

# seasons = ['sowing', 'peak', 'harvesting']

def filter_dataset(data_filters: dict, start_date, end_date, boundary=None) -> ee.ImageCollection:
    """Apply given filters to dataset on GEE

    Args:
        data_filters (dict): json-like Python dictionary that contains filter settings
        boundary: GEE object that defines the boundary of the study region
    Raises:
        BadRequest: invalid parameters

    Returns:
        ee.ImageCollection: the filtered dataset
    """    
    
    fils = []
    
    fils.append(ee.Filter.date(start_date, end_date))
    
    # dataset name
    dataset_name = data_filters['name']
    if dataset_name not in dataset_names['radar'] and dataset_name not in dataset_names['optical']:
        raise BadRequest("dataset name not found")
    
    
    if dataset_name in dataset_names['radar']:
        # radar data - Sentinel 1
        feature = data_filters['feature']
        if feature not in feature_list['radar']:
            raise BadRequest("Wrong features")
        
        fils.append(ee.Filter.eq('instrumentMode', 'IW'))
        
        # bands
        if feature == 'VV':
            fils.append(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
        elif feature == 'VH':
            fils.append(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
        elif feature == 'VH/VV':
            fils.append(ee.Filter.listContains('transmitterReceiverPolarisation', 'VV'))
            fils.append(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH'))
            
        # orbits
        if not data_filters['ascd']:
            fils.append(ee.Filter.neq('orbitProperties_pass', 'ASCENDING'))
        if not data_filters['desc']:
            fils.append(ee.Filter.neq('orbitProperties_pass', 'DESCENDING'))
        
    else:
        # optical data
        # cloud cover
        cloud_fieldname = None 
        if dataset_name.startswith('COPERNICUS/S2'):
            cloud_fieldname = "CLOUDY_PIXEL_PERCENTAGE"
        elif dataset_name.startswith('LANDSAT'):
            cloud_fieldname = "CLOUD_COVER"
        
        if cloud_fieldname is not None:
            fils.append(ee.Filter.lte(cloud_fieldname, int(data_filters['cloud'])))
            
    
    # apply filters to dataset
    pool = ee.ImageCollection(dataset_name).filter(ee.Filter(fils))
    if boundary:
        pool = pool.filterBounds(boundary)

    return pool


def compute_feature(dataset_name: str, pool: ee.ImageCollection, feature: str) -> ee.ImageCollection:
    
    def map_radar(img):
        nonlocal feature
        backscatter_img = dbToPower(img)  # convert dB to raw backscatter values
        feature_img = backscatter_img.expression("feature=" + feature, {'VH': img.select('VH'), 'VV': img.select('VV')})
        return feature_img.copyProperties(img).set('system:time_start', img.get('system:time_start'))
    
    def map_optical(img):
        nonlocal feature
        if feature == 'NDVI':
            nir = dataset_names['optical'][dataset_name]['bands']['nir']
            red = dataset_names['optical'][dataset_name]['bands']['red']
            feature_img = img.normalizedDifference([nir, red]).rename('feature')
        elif feature == 'EVI':
            nir = dataset_names['optical'][dataset_name]['bands']['nir']
            red = dataset_names['optical'][dataset_name]['bands']['red']
            blue = dataset_names['optical'][dataset_name]['bands']['blue']
            feature_img = img.expression(f"feature= 2.5 * (b('{nir}') - b('{red}')) / (b('{nir}') + 6 * b('{red}') - 7.5 * b('{blue}') + 1)")
        elif feature == 'NDWI':
            green = dataset_names['optical'][dataset_name]['bands']['green']
            nir = dataset_names['optical'][dataset_name]['bands']['nir']
            feature_img = img.normalizedDifference([green, nir]).rename('feature')
        elif feature == 'MNDWI':
            green = dataset_names['optical'][dataset_name]['bands']['green']
            swir1 = dataset_names['optical'][dataset_name]['bands']['swir1']
            feature_img = img.normalizedDifference([green, swir1]).rename('feature')
        else:
            feature_img = None
        
        return feature_img.copyProperties(img).set('system:time_start', img.get('system:time_start'))

    
    if feature in feature_list['radar']:
        if feature in ['VV', 'VH']:
            return pool.select(feature).map(lambda img: img.rename('feature').copyProperties(img).set('system:time_start', img.get('system:time_start')))
        else:
            return pool.map(map_radar)
    elif feature in feature_list['optical']:
        return pool.map(map_optical)
            

def makeFalseColorMonthlyComposite(year: int):

    month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_starts = []
    for month in range(1, 13):
        month_starts.append(f"{year}-{month}-1")
    month_starts.append(f"{year+1}-1-1")
    
    month_ranges = list(zip(month_starts[:-1], month_starts[1:]))
    month_ranges = {month_names[i]: month_ranges[i] for i in range(12)}
    
    # vis_params = {"min":0, "max": 1}   # use for NDVI
    vis_params = {"bands": ["B8", "B4", "B3"], "max": 4000}   # use for false-color composite
    
    def map_month(month_range):
        l8_filtered = l8.filterDate(ee.List(month_range).get(0), ee.List(month_range).get(1))
        composite = l8_filtered.median()
        # composite = ee.Algorithms.Landsat.simpleComposite(collection=l8_filtered, asFloat=True)
        return composite #.getMapId(vis_params)['tile_fetcher'].url_format
    
    if year > 2013:
        # Use Landsat-8 after 2013
        # data = ee.ImageCollection("LANDSAT/LC08/C01/T1")
        data = ee.ImageCollection("COPERNICUS/S2")
        # months = ee.List(month_ranges)
        urls = {}
        for month in month_ranges:
            month_start, month_end = month_ranges[month]
            data_filtered = data.filterDate(month_start, month_end)
            # composite = ee.Algorithms.Landsat.simpleComposite(collection=data_filtered, asFloat=True)
            composite = data_filtered.median()
            # min = composite.reduceRegion(ee.Reducer.min())
            # max = composite.max()
            # vis_params["min"] = min
            # vis_params["max"] = max
            
            urls[month] = composite.getMapId(vis_params)['tile_fetcher'].url_format
            
        return urls
        # print(months.getInfo())
        # composites = months.map(map_month).getInfo()
        # print(composites)
        # .filterDate(f"{year}-01-01", f"{int(year)+1}-01-01")
        # composite = 