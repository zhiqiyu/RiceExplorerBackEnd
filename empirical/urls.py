from django.urls import path

from . import views

app_name = 'empirical'

urlpatterns = [
    path('', views.set_params, name="set_params"),
]