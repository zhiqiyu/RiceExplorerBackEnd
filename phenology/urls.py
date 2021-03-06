from django.urls import path

from . import views

app_name = 'phenology'

urlpatterns = [
    path('', views.handleSaveSettings, name="index"),
    path('monthly_composite', views.handleGetMonthlyComposite, name="monthly_composite")
]