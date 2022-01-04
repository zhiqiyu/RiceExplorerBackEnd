from django import http
from django.http.response import HttpResponseBadRequest, HttpResponseNotAllowed, JsonResponse
from django.shortcuts import render
from django.http import HttpResponse, HttpRequest, HttpResponseBadRequest

from django.views.generic.base import TemplateView
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt

import json
import service.main as service


@csrf_exempt
def handleSaveSettings(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            res = service.get_phenology(data)
            return JsonResponse(res)
        except Exception as e:
            return HttpResponseBadRequest(e)
    else:
        return HttpResponseNotAllowed(["GET"])

@csrf_exempt
def handleGetMonthlyComposite(request: HttpRequest) -> HttpResponse:
    try:
        params_dict = request.GET
        year = params_dict['year']
        res = service.get_monthly_composite("2019")
        return JsonResponse(res, safe=False)
    except Exception as e:
        print(e)
        return HttpResponseBadRequest(e)
