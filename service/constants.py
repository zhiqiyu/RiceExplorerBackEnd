import ee

DATASET_LIST = {
    'radar': {
        "COPERNICUS/S1_GRD": {
            'name': "Sentinel-1 SAR GRD: C-band Synthetic Aperture Radar Ground Range Detected, log scaling",
            'scale': 10
        }
    },
    'optical': {
        "MODIS/006/MOD13Q1": {
            'name': 'MOD13Q1.006 Terra Vegetation Indices 16-Day Global 250m',
            'scale': 250
        },
        "LANDSAT/LT05/C01/T1_TOA": {
            'name': 'USGS Landsat 5 TM Collection 1 Tier 1 TOA Reflectance',
            'bands': {
                'blue': 'B1',
                'green': 'B2',
                'red': 'B3',
                'nir': 'B4',
                'swir1': 'B5',
                'swir2': 'B7'
            },
            'scale': 30
        },
        "LANDSAT/LT05/C01/T1_SR": {
            'name': 'USGS Landsat 5 Surface Reflectance Tier 1',
            'bands': {
                'blue': 'B1',
                'green': 'B2',
                'red': 'B3',
                'nir': 'B4',
                'swir1': 'B5',
                'swir2': 'B7'
            },
            'scale': 30
        },
        "LANDSAT/LC08/C01/T1_TOA": {
            'name': 'USGS Landsat 8 Collection 1 Tier 1 TOA Reflectance',
            'bands': {
                'blue': 'B2',
                'green': 'B3',
                'red': 'B4',
                'nir': 'B5',
                'swir1': 'B6',
                'swir2': 'B7'
            },
            'scale': 30
        },
        "COPERNICUS/S2": {
            'name': 'Sentinel-2 MSI: MultiSpectral Instrument, Level-1C',
            'bands': {
                'blue': 'B2',
                'green': 'B3',
                'red': 'B4',
                'nir': 'B8',
                'swir1': 'B11',
                'swir2': 'B12'
            },
            'scale': 10
        },
        "COPERNICUS/S2_SR": {
            'name': 'Sentinel-2 MSI: MultiSpectral Instrument, Level-2A',
            'bands': {
                'blue': 'B2',
                'green': 'B3',
                'red': 'B4',
                'nir': 'B8',
                'swir1': 'B11',
                'swir2': 'B12'
            },
            'scale': 10
        },
    }
}

FEATURE_LIST = {
    'radar': {
        'VH': "VH band",
        'VV': "VV band",
        "VH/VV": "VH/VV (cross ratio)",
    },
    'optical': {
        'NDVI': "NDVI",
        'EVI': "EVI",
        'NDWI': "NDWI",
        'MNDWI': "MNDWI",
    },
}

MODEL_LIST = {
    'Random Forest': ee.Classifier.smileRandomForest,
    'Gradient Tree Boost': ee.Classifier.smileGradientTreeBoost,
    'Support Vector Machine': ee.Classifier.libsvm,
    'CART': ee.Classifier.smileCart,
    'Naive Bayes': ee.Classifier.smileNaiveBayes,
}