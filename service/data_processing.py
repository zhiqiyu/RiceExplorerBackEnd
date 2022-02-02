import ee
from django.core.exceptions import BadRequest
from .constants import DATASET_LIST, FEATURE_LIST
from .speckle_filters import dbToPower
# from .conversion import geojson_to_ee

# seasons = ['sowing', 'peak', 'harvesting']

def filter_dataset(data_filters: dict, boundary=None) -> ee.ImageCollection:
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
    
    if 'start_date' in data_filters and 'end_date' in data_filters:
        fils.append(ee.Filter.date(data_filters['start_date'], data_filters['end_date']))
    
    # dataset name
    dataset_name = data_filters['name']
    if dataset_name not in DATASET_LIST['radar'] and dataset_name not in DATASET_LIST['optical']:
        raise BadRequest("dataset name not found")
    
    
    if dataset_name in DATASET_LIST['radar']:
        # radar data - Sentinel 1
        feature = data_filters['feature']
        if feature not in FEATURE_LIST['radar']:
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
            nir = DATASET_LIST['optical'][dataset_name]['bands']['nir']
            red = DATASET_LIST['optical'][dataset_name]['bands']['red']
            feature_img = img.normalizedDifference([nir, red]).rename('feature')
        elif feature == 'EVI':
            nir = DATASET_LIST['optical'][dataset_name]['bands']['nir']
            red = DATASET_LIST['optical'][dataset_name]['bands']['red']
            blue = DATASET_LIST['optical'][dataset_name]['bands']['blue']
            feature_img = img.expression(f"feature= 2.5 * (b('{nir}') - b('{red}')) / (b('{nir}') + 6 * b('{red}') - 7.5 * b('{blue}') + 1)")
        elif feature == 'NDWI':
            green = DATASET_LIST['optical'][dataset_name]['bands']['green']
            nir = DATASET_LIST['optical'][dataset_name]['bands']['nir']
            feature_img = img.normalizedDifference([green, nir]).rename('feature')
        elif feature == 'MNDWI':
            green = DATASET_LIST['optical'][dataset_name]['bands']['green']
            swir1 = DATASET_LIST['optical'][dataset_name]['bands']['swir1']
            feature_img = img.normalizedDifference([green, swir1]).rename('feature')
        else:
            feature_img = None
        
        return feature_img.copyProperties(img).set('system:time_start', img.get('system:time_start'))

    
    if feature in FEATURE_LIST['radar']:
        if feature in ['VV', 'VH']:
            return pool.select(feature).map(lambda img: img.rename('feature').copyProperties(img).set('system:time_start', img.get('system:time_start')))
        else:
            return pool.map(map_radar)
    elif feature in FEATURE_LIST['optical']:
        return pool.map(map_optical)


def make_false_color_monthly_composite(start_date: str, end_date: str):
    from datetime import datetime
    from dateutil.relativedelta import relativedelta
    
    sdate = datetime.strptime(start_date, "%Y-%m")
    edate = datetime.strptime(end_date, "%Y-%m")
    
    num_months = (edate.year - sdate.year) * 12 + (edate.month - sdate.month + 1)
    
    # month_names = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    month_starts = []
    for i in range(num_months):
        temp_date = sdate + relativedelta(months=+i)
        month_starts.append(f"{temp_date.year}-{temp_date.month}")
        
    last_month = edate + relativedelta(months=+1)
    month_starts.append(f"{last_month.year}-{last_month.month}")
    
    month_ranges = list(zip(month_starts[:-1], month_starts[1:]))
    month_ranges = {x[0]: x for x in month_ranges}
    
    # vis_params = {"min":0, "max": 1}   # use for NDVI
    
    if sdate.year > 2015 or (sdate.year == 2015 and sdate.month > 6):
        # Use sentinel-2 if start year > 2015
        data = ee.ImageCollection("COPERNICUS/S2")
        scale, offset = 0.0001, 0
        vis_params = {"bands": ["B8", "B4", "B3"], "max": 0.5}
    elif sdate.year > 2013 or (sdate.year == 2013 and sdate.month >= 5):
        # use Landsat-8 
        data = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2")
        scale, offset = 0.0000275, -0.2
        vis_params = {"bands": ["SR_B5", "SR_B4", "SR_B3"], "max": 0.5}
    else:
        # if end year > 2011, use Landsat-7
        data = ee.ImageCollection("LANDSAT/LE07/C02/T1_L2")
        scale, offset = 0.0000275, -0.2
        vis_params = {"bands": ["SR_B4", "SR_B3", "SR_B2"], "max": 0.5}

    urls = {}
    for month in month_ranges:
        month_start, month_end = month_ranges[month]
        data_filtered = data.filterDate(month_start, month_end)
        # composite = ee.Algorithms.Landsat.simpleComposite(collection=data_filtered, asFloat=True)
        composite = data_filtered.median().multiply(scale).add(offset)
        # min = composite.reduceRegion(ee.Reducer.min())
        # max = composite.max()
        # vis_params["min"] = min
        # vis_params["max"] = max
        
        urls[month] = composite.getMapId(vis_params)['tile_fetcher'].url_format
        
    return urls