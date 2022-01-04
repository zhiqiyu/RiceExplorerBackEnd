from django.apps import AppConfig
import ee
from utils.credential import EE_CREDENTIALS


class ClassificationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'classification'

    def ready(self) -> None:
        ee.Initialize(EE_CREDENTIALS)
    