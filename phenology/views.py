from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic.base import TemplateView

import ee
import folium

from .utils.basemaps import basemaps

# change the default js and css in folium
default_js = [
    ('leaflet',
     'https://unpkg.com/leaflet@1.7.1/dist/leaflet.js'),
    ('jquery',
     'https://code.jquery.com/jquery-1.12.4.min.js'),
    ('bootstrap',
     'https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/js/bootstrap.bundle.min.js'),
    ('awesome_markers',
     'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.js'),  # noqa
    ]

default_css = [
    ('leaflet_css',
     'https://unpkg.com/leaflet@1.7.1/dist/leaflet.css'), 
    ('bootstrap_css',
     'https://cdn.jsdelivr.net/npm/bootstrap@5.0.2/dist/css/bootstrap.min.css'),
    # ('bootstrap_theme_css',
    #  'https://maxcdn.bootstrapcdn.com/bootstrap/3.2.0/css/bootstrap-theme.min.css'),  # noqa
    ('awesome_markers_font_css',
     'https://maxcdn.bootstrapcdn.com/font-awesome/4.6.3/css/font-awesome.min.css'),  # noqa
    ('awesome_markers_css',
     'https://cdnjs.cloudflare.com/ajax/libs/Leaflet.awesome-markers/2.0.2/leaflet.awesome-markers.css'),  # noqa
    ('awesome_rotate_css',
     'https://cdn.jsdelivr.net/gh/python-visualization/folium/folium/templates/leaflet.awesome.rotate.min.css'),  # noqa
    ]

# Create your views here.
class MyView(TemplateView):
    
    template_name = "phenology/index.html"
    
    def __init__(self):
        self.figure = folium.Figure()
    
        # map object
        self.m = folium.Map(
            location=[28.5973518, 83.54495724],
            zoom_start=8,
            tiles=None,
        )
        
        # override default Bootstrap and Leaflet versions
        self.m.default_css = default_css
        self.m.default_js = default_js
        
        for tile in basemaps.values():
            tile.add_to(self.m)
        
        self.m.add_to(self.figure)
        
    def get(self, request, *args, **kwargs):
        
        dataset = (ee.ImageCollection('MODIS/006/MOD13Q1')
                .filter(ee.Filter.date('2019-07-01', '2019-11-30'))
                .first())
        modisndvi = dataset.select('NDVI')
        
        vis_paramsNDVI = {
                'min': 0,
                'max': 9000,
                'palette': [ 'FE8374', 'C0E5DE', '3A837C','034B48',]}
        
        map_id_dict = ee.Image(modisndvi).getMapId(vis_paramsNDVI)
        
        folium.raster_layers.TileLayer(
                        tiles = map_id_dict['tile_fetcher'].url_format,
                        attr = 'Google Earth Engine',
                        name = 'NDVI',
                        overlay = True,
                        control = True
                        ).add_to(self.m)
        
        self.m.add_child(folium.LayerControl())
        
        self.figure.render()
        
        context = {
            'title': "Crop Phenology",
            'map': self.figure,
        }
        
        return render(request, self.template_name, context)
        
    