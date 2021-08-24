from django.urls import path

from . import views

app_name = 'phenology'

urlpatterns = [
    path('', views.saveSettings, name="index"),
]