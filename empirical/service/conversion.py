import json
import os
from django.core.exceptions import BadRequest
import ee

def shp_to_ee(in_shp):
    """Converts a shapefile to Earth Engine objects.

    Args:
        in_shp (str): File path to a shapefile.

    Returns:
        object: Earth Engine objects representing the shapefile.
    """
    try:
        json_data = shp_to_geojson(in_shp)
        ee_object = geojson_to_ee(json_data)
        return ee_object
    except Exception as e:
        print(e)

def shp_reader_to_geojson(shp_reader):
    fields = shp_reader.fields[1:]
    field_names = [field[0] for field in fields]
    buffer = []
    for sr in shp_reader.shapeRecords():
        atr = dict(zip(field_names, sr.record))
        geom = sr.shape.__geo_interface__
        buffer.append(dict(type="Feature", geometry=geom, properties=atr))
    
    import json
    geojson = json.dumps({"type": "FeatureCollection",
                            "features": buffer}, indent=2)
    return geojson

def shp_to_geojson(in_shp, out_json=None):
    """Converts a shapefile to GeoJSON.

    Args:
        in_shp (str): File path of the input shapefile.
        out_json (str, optional): File path of the output GeoJSON. Defaults to None.

    Returns:
        object: The json object representing the shapefile.
    """
    # check_install('pyshp')
    try:
        import json
        import shapefile
        in_shp = os.path.abspath(in_shp)

        if out_json is None:
            out_json = os.path.splitext(in_shp)[0] + ".json"

            if os.path.exists(out_json):
                out_json = out_json.replace('.json', '_bk.json')

        elif not os.path.exists(os.path.dirname(out_json)):
            os.makedirs(os.path.dirname(out_json))

        reader = shapefile.Reader(in_shp)
        
        geojson_str = shp_reader_to_geojson(reader)
        geojson = open(out_json, "w")
        geojson.write(geojson_str + "\n")
        geojson.close()

        with open(out_json) as f:
            json_data = json.load(f)

        return json_data

    except Exception as e:
        print(e)
        
def geojson_to_ee(geo_json, geodesic=True):
    """Converts a geojson to ee.Geometry()

    Args:
        geo_json (dict): A geojson geometry dictionary or file path.

    Returns:
        ee_object: An ee.Geometry object
    """

    try:

        import json

        if not isinstance(geo_json, dict) and os.path.isfile(geo_json):
            with open(os.path.abspath(geo_json)) as f:
                geo_json = json.load(f)
        
        if geo_json['type'] == 'FeatureCollection':
            features = ee.FeatureCollection(geo_json['features'])
            return features
        elif geo_json['type'] == 'Feature':
            geom = None
            keys = geo_json['properties']['style'].keys()
            if 'radius' in keys:  # Checks whether it is a circle
                geom = ee.Geometry(geo_json['geometry'])
                radius = geo_json['properties']['style']['radius']
                geom = geom.buffer(radius)
            elif geo_json['geometry']['type'] == 'Point':  # Checks whether it is a point
                coordinates = geo_json['geometry']['coordinates']
                longitude = coordinates[0]
                latitude = coordinates[1]
                geom = ee.Geometry.Point(longitude, latitude)
            else:
                geom = ee.Geometry(geo_json['geometry'], "", geodesic)
            return ee.Feature(geom)
        else:
            print("Could not convert the geojson to ee.Geometry()")

    except Exception as e:
        print("Could not convert the geojson to ee.Geometry()")
        print(e)


def shp_zip_to_ee(file):
    from zipfile import ZipFile
    import re
    from shapefile import Reader
    
    zip = ZipFile(file)
    file_names = zip.namelist()
    shp_filename = None
    shx_filename = None
    dbf_filename = None
    for file_name in file_names:
        shp_match = re.match(r".+\.shp$", file_name)
        shx_match = re.match(r".+\.shx$", file_name)
        dbf_match = re.match(r".+\.dbf$", file_name)
        
        if shp_match:
            shp_filename = file_name
        elif shx_match:
            shx_filename = file_name
        elif dbf_match:
            dbf_filename = file_name
    
    if not shp_filename or not shx_filename or not dbf_filename:
        raise BadRequest("Invalid boundary file")
    
    reader = Reader(shp=zip.open(shp_filename), shx=zip.open(shx_filename), dbf=zip.open(dbf_filename))
    
    geojson_str = shp_reader_to_geojson(reader)
    
    ee_obj = geojson_to_ee(json.loads(geojson_str))
    
    return ee_obj
    