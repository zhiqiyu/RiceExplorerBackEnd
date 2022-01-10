import json
from django.core.exceptions import BadRequest
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

from classification.forms import PostForm

import service.main as service


@csrf_exempt
def handle_request(request):
    if request.method == "POST":
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            filters = json.load(request.FILES['json'])
            if 'boundary_file' in request.FILES:
                filters['dataset']['boundary_file'] = request.FILES['boundary_file']

            if 'samples' not in request.FILES:
                return HttpResponseBadRequest('No ground truth samples provided.')

            try:
                res = service.run_supervised_classification(
                    filters, json.load(request.FILES['samples']))
                return JsonResponse(res)
            except Exception as e:
                return HttpResponseBadRequest(e)

        else:
            return HttpResponseBadRequest("Form is invalid")
    else:
        return HttpResponseNotAllowed(["GET"])
