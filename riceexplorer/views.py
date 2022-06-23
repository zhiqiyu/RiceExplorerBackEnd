from django.http import FileResponse, HttpResponseNotFound
from django.shortcuts import render
from django.http.response import JsonResponse
from service.main import get_task_list, get_the_task, download_file
from utils.credential import EE_CREDENTIALS
import ee

def home(request):
    
    # if EE_CREDENTIALS:
    #     ee.Initialize(EE_CREDENTIALS)
    
    return render(request, 'index.html')

def get_tasks(request):
    return JsonResponse(get_task_list(), safe=False)

def get_task_with_id(request, id):
    return JsonResponse(get_the_task(id), safe=False)

def handle_download_file(request, id):
    
    filename = download_file(id)
    if filename is not None:
        return FileResponse(open(filename, 'rb'), as_attachment=True, )
    else:
        return HttpResponseNotFound()