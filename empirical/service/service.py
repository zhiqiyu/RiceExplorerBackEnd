from empirical.service.speckle_filters import dbToPower, refinedLee
import ee
from django.core.exceptions import BadRequest

from .conversion import *
from .constants import dataset_names, feature_list


default_boundary_file = "./empirical/data/Terai_belt_Nepal.shp"

seasons = ['sowing', 'peak', 'harvesting']

vis_params = {"min": 0, "max": 1, "opacity": 1, "palette": ["ffffff", "328138"]}


def validate_filters():
    pass


def run_classification(filters):
    """Run classification

    Args:
        filters (dict): Json-like Python dictionary that holds all filters from request

    Returns:
        tuple(dict, str): A tuple of dict that contains tile layer urls for each season and a tile url string for combined result
    """    
    print(filters)
    
    data_filters = filters['dataset']
    # boundary
    if data_filters['boundary'] == 'upload':
        boundary = shp_zip_to_ee(data_filters['boundary_file']).geometry()
    else:
        default_boundary = shp_to_ee(default_boundary_file)
        boundary = default_boundary.filterMetadata('DISTRICT', 'equals', data_filters['boundary']).first().geometry()
    
    # crop mask
    crop_mask = ee.Image("projects/testee-319020/assets/terai_agri_mask").clip(boundary)
    
    # filter dataset
    pool = filter_dataset(data_filters, boundary)
    
    # apply specific filter and thresholds for each season
    season_res = {season: None for season in seasons}

    for season in seasons:
        if season in filters:
            
            # date range of this season
            start_date, end_date = filters[season]['start'], filters[season]['end']
            
            # threshold min and max
            thres_min, thres_max = float(filters[season]['min']), float(filters[season]['max'])

            # filter by season date range
            season_data_pool = pool.filter(ee.Filter.date(start_date, end_date))
            
            # speckle filter if radar data
            # TODO: allow selectio of speckle filter type
            # if data_filters['name'] in dataset_names['radar']:
            #     season_data_pool = season_data_pool.map(lambda img: refinedLee(img).copyProperties(img).set('system:time_start', img.get('system:time_start')))
            
            # compute selected feature
            season_data_pool = compute_feature(data_filters['name'], season_data_pool, data_filters['feature'])
            
            # make composite 
            if data_filters['composite'] == 'minimum':
                season_data = season_data_pool.min()
            elif data_filters['composite'] == 'maximum':
                season_data = season_data_pool.max()
            elif data_filters['composite'] == 'median':
                season_data = season_data_pool.median()
            elif data_filters['composite'] == 'mean':
                season_data = season_data_pool.mean()
            elif data_filters['composite'] == 'mode':
                season_data = season_data_pool.mode()
            else:
                raise BadRequest("Unrecognized composite type")
            
            # print(season_data.getDownloadUrl({'name': 'data', 'region': boundary}))
            season_res[season] = (season_data.lte(thres_max)).And(season_data.gte(thres_min)).updateMask(crop_mask).clip(boundary)

        else:
            del season_res[season]

    # make a final map based on all seasons
    season_res_list = list(season_res.values())
    combined_res = season_res_list[0]
    for i in range(1, len(season_res_list)):
        combined_res = combined_res.Or(season_res_list[i])
    
    
    res = {}
    if data_filters['name'] in dataset_names['radar']:
        scale = dataset_names['radar'][data_filters['name']]['scale']
    else:
        scale = dataset_names['optical'][data_filters['name']]['scale']
    
    # compute area
    area = ee.Number(combined_res.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(),boundary,scale,None,None,False,1e13).get('feature')).divide(1e4).getInfo()
    
        
    for season, layer in season_res.items():
        
        res[season] = {
            "tile_url": layer.getMapId(vis_params)['tile_fetcher'].url_format,
            "download_url": layer.getDownloadURL({
                'name': season,
                'scale': 200,
                'region': boundary,
            }),
            
        }
        
    res['combined'] = {
        'tile_url': combined_res.getMapId(vis_params)['tile_fetcher'].url_format,
        'download_url': combined_res.getDownloadURL({
            'name': 'combined',
            'scale': 200,
            'region': boundary,
        }),
        "area": area
    }
        
    return res


def filter_dataset(data_filters: dict, boundary) -> ee.ImageCollection:
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
    pool = ee.ImageCollection(dataset_name).filter(ee.Filter(fils)).filterBounds(boundary)

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
            

    