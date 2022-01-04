from django.urls import path

from . import views

app_name = 'classification'

urlpatterns = [
    path('', views.handle_request, name="run_supervised_classification"),
]