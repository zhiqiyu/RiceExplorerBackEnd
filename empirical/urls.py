from django.urls import path

from . import views

app_name = 'empirical'

urlpatterns = [
    path('', views.run_algorithm, name="set_params"),
]