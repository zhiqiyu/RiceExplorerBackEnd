from django.shortcuts import render
from utils.credential import EE_CREDENTIALS
import ee

def home(request):
    
    # if EE_CREDENTIALS:
    #     ee.Initialize(EE_CREDENTIALS)
    
    return render(request, 'index.html')