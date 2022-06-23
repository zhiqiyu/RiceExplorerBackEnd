from django.core.exceptions import BadRequest
from django.http.response import HttpResponseBadRequest
from empirical.forms import PostForm
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
import json

import service.main as service


@csrf_exempt
def run_algorithm(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            filters = json.load(request.FILES['json'])
            if 'boundary_file' in request.FILES:
                filters['dataset']['boundary_file'] = request.FILES['boundary_file']
                
            try:
                img, boundary, scale = service.run_threshold_based_classification(filters)
                res = service.make_empirical_results(img, boundary, scale)
                return JsonResponse(res)
            except Exception as e:
                return HttpResponseBadRequest(e)
        else:
            return HttpResponseBadRequest("Form is invalid, please check if all parameters are set.")

    else:
        return HttpResponseNotAllowed(["GET"])  

@csrf_exempt
def handle_export_result(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            filters = json.load(request.FILES['json'])
            if 'boundary_file' in request.FILES:
                filters['dataset']['boundary_file'] = request.FILES['boundary_file']
                
            try:
                img, boundary, scale = service.run_threshold_based_classification(filters)
                taskId = service.export_result(img, boundary, scale)
                return JsonResponse(taskId, safe=False)
            except Exception as e:
                return HttpResponseBadRequest(e)
        else:
            return HttpResponseBadRequest("Form is invalid, please check if all parameters are set.")

    else:
        return HttpResponseNotAllowed(["GET"])