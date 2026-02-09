"""
URL configuration for dashboard API.
"""
from django.urls import path
from . import views

urlpatterns = [
    path('metrics/', views.metrics),
    path('trips-over-time/', views.trips_over_time),
    path('trips-by-hour/', views.trips_by_hour),
    path('trips-by-weekday/', views.trips_by_weekday),
    path('payment-type/', views.payment_type),
    path('heatmap/', views.heatmap),
    path('demand-predictions/', views.demand_predictions),
    path('cluster-zones/', views.cluster_zones),
    path('duration-predictions/', views.duration_predictions),
    path('dashboard/', views.dashboard_all),
    path('upload/', views.upload),
    path('load-sample/', views.load_sample),
]
