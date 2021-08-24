from django.core.exceptions import BadRequest
from django.http.response import HttpResponseBadRequest
from empirical.forms import PostForm
from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import ensure_csrf_cookie
import json

import empirical.service.service as service


@ensure_csrf_cookie
def run_algorithm(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            filters = json.load(request.FILES['json'])
            if 'file' in request.FILES:
                filters['dataset']['boundary_file'] = request.FILES['file']
                
            try:
                res = service.run_classification(filters)
                return JsonResponse(res)
            except BadRequest as e:
                return HttpResponseBadRequest(e)
        else:
            return HttpResponseBadRequest()

    else:
        return HttpResponseNotAllowed(["GET"])
