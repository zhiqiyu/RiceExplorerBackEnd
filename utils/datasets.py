radar_features = {
    "VH": {
        "name": "VH band",
        "formula": None,
    },
    "VV": {
        "name": "VV band",
        "formula": None,
    },
    "VH/VV": {
        "name": "VH/VV (cross ratio)",
        "formula": "VH/VV",
    },
    "RVI": {
        "name": "RVI (Radar Vegetation Index)",
        "formula": "4 * VH / (VH + VV)",
    }
}

optical_features = {
    "NDVI": {
        "name": "NDVI (Normalized Difference Vegetation Index)",
        "formula": ""
    },
    "EVI": {
        "name": "EVI (Enhanced Vegetation Index)",
    },
    "LSWI": {
        "name": "LSWI (Land Surface Water Index)",
        "formula": "",
    },
    "MNDWI": {
        "name": "MNDWI (Modified Normalized Difference Water Index",
        "formula": "",
    }
}

dataList = {
    "radar": {
        "COPERNICUS/S1_GRD": {
            "name": "Sentinel-1 SAR GRD: C-band Synthetic Aperture Radar Ground Range Detected, log scaling",
            "features": radar_features,
        }
    },
    "optical": {
        "MODIS": {
            "MODIS/006/MOD13Q1": {
                "name": "MOD13Q1.006 Terra Vegetation Indices 16-Day Global 250m",
                "features": optical_features,
            }
        },
        "MODIS/006/MOD13Q1":
        "MOD13Q1.006 Terra Vegetation Indices 16-Day Global 250m",
        "LANDSAT/LT05/C01/T1_TOA":
        "USGS Landsat 5 TM Collection 1 Tier 1 TOA Reflectance",
        "LANDSAT/LT05/C01/T1_SR": "USGS Landsat 5 Surface Reflectance Tier 1",
        "LANDSAT/LC08/C01/T1_TOA":
        "USGS Landsat 8 Collection 1 Tier 1 TOA Reflectance",
        "COPERNICUS/S2": "Sentinel-2 MSI: MultiSpectral Instrument, Level-1C",
        "COPERNICUS/S2_SR": "Sentinel-2 MSI: MultiSpectral Instrument, Level-2A",
    },
}
