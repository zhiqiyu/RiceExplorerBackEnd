'''
EE crediential configuration
'''
import os
import ee
from django.conf import settings

EE_ACCOUNT = 'myeeaccount@testee-319020.iam.gserviceaccount.com'

EE_PRIVATE_KEY_FILE = os.path.join(settings.BASE_DIR, 'utils', 'ee_credential.json')

EE_CREDENTIALS = ee.ServiceAccountCredentials(
    EE_ACCOUNT, EE_PRIVATE_KEY_FILE)