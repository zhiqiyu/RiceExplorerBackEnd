import ee
from .data_processing import compute_feature, filter_dataset, makeFalseColorMonthlyComposite
from .conversion import geojson_to_ee

seasons = ['sowing', 'peak', 'harvesting']

def saveSettingsToSession(data):
    print(data)
    data_filters = data['dataset']
    samples = data['samples']
    
    samples_ee = geojson_to_ee(samples)

    # apply specific filter and thresholds for each season
    season_pools = {season: None for season in seasons}
    
    for season in seasons:
        if season in data:
            
            # date range of this season
            start_date, end_date = data[season]['start'], data[season]['end']

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


def getMonthlyCompositeForYear(year):
    return makeFalseColorMonthlyComposite(int(year))