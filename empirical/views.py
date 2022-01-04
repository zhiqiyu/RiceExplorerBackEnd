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
                res = service.run_threshold_based_classification(filters)
                return JsonResponse(res)
            except BadRequest as e:
                return HttpResponseBadRequest(e)
        else:
            return HttpResponseBadRequest()

    else:
        return HttpResponseNotAllowed(["GET"])
