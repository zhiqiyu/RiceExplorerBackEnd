from django.core.exceptions import BadRequest
import ee
from .data_processing import compute_feature, filter_dataset, make_false_color_monthly_composite
from .conversion import geojson_to_ee, shp_to_ee, shp_zip_to_ee
from .constants import dataset_names, feature_list
from .speckle_filters import boxcar

seasons = ['sowing', 'peak', 'harvesting']

default_boundary_file = "data/Terai_belt_Nepal.shp"

default_download_scale = 250

rice_vis_params = {"min": 0, "max": 1, "opacity": 1, "palette": ["ffffff", "328138"]}

def get_phenology(data):
    '''
    Get time-series image data for the input ground truth samples
    '''
    # print(data)
    data_filters = data['dataset']
    samples = data['samples']
    
    samples_ee = geojson_to_ee(samples)
    
    # TODO: change hard coded dates
    start_date, end_date = '2021-1-1', '2021-12-31'
    data_filters['start_date'] = start_date
    data_filters['end_date'] = end_date
    data_pool = filter_dataset(data_filters, samples_ee.geometry())
    feature_pool = compute_feature(data_filters['name'], data_pool, data_filters['feature'])
    year_img = feature_pool.map(lambda img: img.rename(ee.Number(img.get('system:time_start')).format("%d").cat('_feature'))).toBands()
    sample_res = year_img.sampleRegions(samples_ee, geometries=True)
    
    return sample_res.getInfo()


def get_monthly_composite(year):
    return make_false_color_monthly_composite(int(year))


def make_composite(data_pool: ee.ImageCollection, start_date, end_date, days, method="median") -> ee.ImageCollection:
    
    def getComposite(date):
        date = ee.Date(date)
        end_millis = date.advance(days, "day").millis().min(ee.Date(end_date).millis()) 
        filtered_pool = data_pool.filterDate(date, ee.Date(end_millis))
        
        if method == 'minimum':
            season_data = filtered_pool.min()
        elif method == 'maximum':
            season_data = filtered_pool.max()
        elif method == 'median':
            season_data = filtered_pool.median()
        elif method == 'mean':
            season_data = filtered_pool.mean()
        elif method == 'mode':
            season_data = filtered_pool.mode()
        else:
            raise BadRequest("Unrecognized composite type")
        
        return ee.Algorithms.If(filtered_pool.size().gt(0), season_data)
    
    def map_func(dateMillis):
        date = ee.Date(dateMillis)
        return getComposite(date)
    
    
    gap_difference = ee.Date(start_date).advance(days, 'day').millis().subtract(ee.Date(start_date).millis())
    list_map = ee.List.sequence(ee.Date(start_date).millis(), ee.Date(end_date).millis(), gap_difference)
    composites = ee.ImageCollection.fromImages(list_map.map(map_func).removeAll([None]))
    
    return composites


def compute_hectare_area(img, boundary, scale) -> ee.Number:
    area = ee.Number(img.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(),boundary,scale,None,None,False,1e13).get('feature')).divide(1e4).getInfo()
    return area

def run_threshold_based_classification(filters):
    """Run classification using thresholds

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
    crop_mask = None
    if data_filters["crop_mask"]:
        crop_mask = ee.Image(data_filters["crop_mask"]).clip(boundary)
    
    # filter dataset
    pool = filter_dataset(data_filters, boundary)
    
    # apply specific filter and thresholds for each season
    season_res = {season: None for season in seasons}
    
    def map_composites(composite):
        composite = ee.Image(composite)
        return (composite.lte(thres_max)).And(composite.gte(thres_min)).updateMask(crop_mask).clip(boundary)

    for season in seasons:
        if season in filters:
            
            # date range of this season
            start_date, end_date = filters[season]['start'], filters[season]['end']
            
            # threshold min and max
            thres_min, thres_max = float(filters[season]['min']), float(filters[season]['max'])

            # filter by season date range
            season_data_pool = pool.filter(ee.Filter.date(start_date, end_date))
            
            # speckle filter if radar data
            # TODO: allow selection of speckle filter type
            if data_filters['name'] in dataset_names['radar']:
            #     season_data_pool = season_data_pool.map(lambda img: refined_lee(img).copyProperties(img).set('system:time_start', img.get('system:time_start')))
                season_data_pool = season_data_pool \
                    .map(lambda img: boxcar(img) \
                                    .rename(img.bandNames()) \
                                    .copyProperties(img) \
                                    .set('system:time_start', img.get('system:time_start')))

            # compute selected feature
            season_data_pool = compute_feature(data_filters['name'], season_data_pool, data_filters['feature'])
            
            # make composite
            composites = make_composite(season_data_pool, start_date, end_date, days=int(data_filters["composite_days"]), method=data_filters['composite'])
            
            
            # print(season_data.getDownloadUrl({'name': 'data', 'region': boundary}))
            # season_res[season] = (season_data.lte(thres_max)).And(season_data.gte(thres_min)).updateMask(crop_mask).clip(boundary)
            thresholded_composites = composites.map(map_composites)
            
            season_res[season] = thresholded_composites.Or()
            
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
    
    # compute area with unit hectar
    # area = ee.Number(combined_res.multiply(ee.Image.pixelArea()).reduceRegion(ee.Reducer.sum(),boundary,scale,None,None,False,1e13).get('feature')).divide(1e4).getInfo()
    area = compute_hectare_area(combined_res, boundary, scale)
    
    # get mapId for the images
    for season, layer in season_res.items():
        
        res[season] = {
            "tile_url": layer.getMapId(rice_vis_params)['tile_fetcher'].url_format,
            "download_url": layer.getDownloadURL({
                'name': season,
                'scale': default_download_scale,
                'region': boundary,
            }),
            
        }
        
    res['combined'] = {
        'tile_url': combined_res.getMapId(rice_vis_params)['tile_fetcher'].url_format,
        'download_url': combined_res.getDownloadURL({
            'name': 'combined',
            'scale': default_download_scale,
            'region': boundary,
        }),
        "area": area
    }
        
    return res


def run_supervised_classification(filters, samples):
    print(filters)
    return {'message': "hello"}
    