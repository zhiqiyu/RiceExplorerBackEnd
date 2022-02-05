# RiceExplorerBackEnd

This is the Django backend of the rice mapping app. 

## Installation

If you have `conda` installed, you can create a new conda environment by running:
```
conda create --name <env> --file conda_requirements_{os version}.txt
```
The `os version` can be either AARM64 (Apple Silicon M1 chip), or linux64.  

## Get Started

This app uses Google Earth Engine service account. You can learn more about service account [here](https://developers.google.com/earth-engine/guides/service_account).

Please create a service account and download the JSON private key as `ee_credential.json`, and put it in the root folder of the app. Then set the account name 
to your account name in `<app_name>/utils/credential.py`.

Then you can run the app by running `python manage.py runserver`.
