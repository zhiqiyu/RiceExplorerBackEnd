from django.http import HttpResponse, JsonResponse, HttpResponseNotAllowed
from django.views.decorators.csrf import ensure_csrf_cookie
import json

import empirical.service.service as service


@ensure_csrf_cookie
def set_params(request):
    if request.method == "POST":
        data = json.loads(request.body)
        # print(data)
        season_res, combined_res = service.run_classification(data)
        res = season_res
        res['combined'] = combined_res
        return JsonResponse(res)
    else:
        return HttpResponseNotAllowed(["GET"])
