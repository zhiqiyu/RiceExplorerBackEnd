from django.apps import AppConfig

import ee
from utils.credential import EE_CREDENTIALS



class PhenologyConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'phenology'
    
    def ready(self):
        
        # initialize GEE client API
        ee.Initialize(EE_CREDENTIALS)
