import os
import ee

from .conversion import *
# from geemap import shp_to_ee, shp_to_geojson

dataset_name = "COPERNICUS/S1_GRD"

boundary_file = "./empirical/data/Chitawan.shp"

seasons = ['sowing', 'peak', 'harvesting']

vis_params = {"min": 0, "max": 1, "opacity": 1, "bands": [
    "VH_median"], "palette": ["ffffff", "328138"]}


def run_classification(filters):
    dataset = ee.ImageCollection(dataset_name)
    boundary = shp_to_ee(boundary_file)
    # print(boundary)
    pool = dataset \
        .filterBounds(boundary) \
        .filter(ee.Filter.listContains('transmitterReceiverPolarisation', 'VH')) \
        .filter(ee.Filter.eq('instrumentMode', 'IW')) \
        .select('VH')

    season_res = {season: None for season in seasons}

    for season in seasons:
        if season in filters:

            start_date, end_date = filters[season]['start'], filters[season]['end']
            ascd, desc = filters[season]['ascd'], filters[season]['desc']
            thres_min, thres_max = float(filters[season]['min']), float(filters[season]['max'])
            
            fils = []
            fils.append(ee.Filter.date(start_date, end_date))
            if not ascd:
                fils.append(ee.Filter.neq('orbitProperties_pass', 'ASCENDING'))
            if not desc:
                fils.append(ee.Filter.neq(
                    'orbitProperties_pass', 'DESCENDING'))

            season_data_pool = pool.filter(ee.Filter(fils))
            print(season_data_pool.size().getInfo())
            
            season_data = season_data_pool.median() \
                .reduceNeighborhood(
                    reducer=ee.Reducer.median(),
                    kernel=ee.Kernel.square(2)
                )
            
            # print(season_data.getDownloadUrl({'name': 'data', 'region': boundary}))
            season_res[season] = (season_data.lte(thres_max)) and (season_data.gte(thres_min))

        else:
            del season_res[season]

    season_res_list = list(season_res.values())
    combined_res = season_res_list[0]
    for i in range(1, len(season_res_list)):
        combined_res = combined_res or season_res_list[i]
    # print(ee.Image(combined_res).getMapId())
    return {season: layer.getMapId(vis_params)['tile_fetcher'].url_format for season, layer in season_res.items()}, \
            season_data.getMapId({'min':thres_min, 'max': thres_max})['tile_fetcher'].url_format
