from django.shortcuts import render
from django.http.response import JsonResponse
from service.main import get_task_list
from utils.credential import EE_CREDENTIALS
import ee

def home(request):
    
    # if EE_CREDENTIALS:
    #     ee.Initialize(EE_CREDENTIALS)
    
    return render(request, 'index.html')

def get_tasks(request):
    return JsonResponse(get_task_list(), safe=False)
    