'''
EE crediential configuration
'''
import os
import ee
from django.conf import settings
import environ
import glob

# Initialize environment variables from .env file
env_file_path = os.path.join(settings.BASE_DIR, ".env")
if len(glob.glob(env_file_path)) > 0:
    env = environ.Env()
    environ.Env.read_env(env_file_path)

EE_ACCOUNT = os.environ.get("EE_ACCOUNT")

EE_PRIVATE_KEY = os.environ.get("EE_CREDENTIALS")

try:
    EE_CREDENTIALS = ee.ServiceAccountCredentials(
        EE_ACCOUNT, key_data=EE_PRIVATE_KEY)
except Exception as e:
    EE_CREDENTIALS = None
    print("Cannot authenticate GEE")