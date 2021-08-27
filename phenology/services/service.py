import ee
from django.core.exceptions import BadRequest
from .constants import dataset_names, feature_list
from .speckle_filters import dbToPower, powerToDb, refinedLee
from .conversion import geojson_to_ee

seasons = ['sowing', 'peak', 'harvesting']

def saveSettingsToSession(data):
    data_filters = data['dataset']
    samples = data['samples']
    
    samples_ee = geojson_to_ee(samples)
    # print(samples_ee.getInfo())
    # filter dataset
    # pool = filter_dataset(data_filters, start_date, samples_ee.geometry())
    
    # apply specific filter and thresholds for each season
    season_pools = {season: None for season in seasons}
    
    for season in seasons:
        if season in data:
            
            # date range of this season
            start_date, end_date = data[season]['start'], data[season]['end']
            
            # threshold min and max
            # thres_min, thres_max = float(data[season]['min']), float(data[season]['max'])

            season_data_pool = filter_dataset(data_filters, start_date, end_date, samples_ee.geometry())
            
            # filter by season date range
            # season_data_pool = pool.filter(ee.Filter.date(start_date, end_date))
            
            # speckle filter if radar data
            # TODO: allow selectio of speckle filter type
            # if data_filters['name'] in dataset_names['radar']:
                # season_data_pool = season_data_pool.map(lambda img: refinedLee(img).copyProperties(img).set('system:time_start', img.get('system:time_start')))
                # season_data_pool = season_data_pool.map(lambda img: refinedLee(img).copyProperties(img).set('system:time_start', img.get('system:time_start')))
            
            # compute selected feature
            season_data_pool = compute_feature(data_filters['name'], season_data_pool, data_filters['feature'])
            
            # season_pools[season] = (season_data_pool.lte(thres_max)).And(season_data.gte(thres_min)).clip(boundary)
            season_pools[season] = season_data_pool
            
        else:
            del season_pools[season]
    

    season_res = {}
    sample_res = samples_ee
    for season in season_pools:
        season_img = season_pools[season].map(lambda img: img.rename(ee.Number(img.get('system:time_start')).format("%d").cat('_').cat(season).cat("_feature__"))).toBands()
        sample_res = season_img.sampleRegions(sample_res, geometries=True)
        # season_res[season] = season_sample.getInfo()
        # total_res = 
    return sample_res.getInfo()


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
            

    