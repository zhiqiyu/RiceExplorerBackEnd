from django.urls import path

from . import views

app_name = 'classification'

urlpatterns = [
    path('', views.handle_run_classification, name="run_supervised_classification"),
    path('export', views.handle_export_classification, name='export_classification')
]