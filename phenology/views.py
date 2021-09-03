from phenology.services.service import saveSettingsToSession
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.http import HttpResponse

from django.views.generic.base import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

import ee
import json


@csrf_exempt
def saveSettings(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            res = saveSettingsToSession(data)
            return JsonResponse(res)
        except Exception as e:
            return HttpResponseBadRequest(e)
    else:
        return HttpResponseNotAllowed(["GET"])
