from django.urls import path

from . import views

app_name = 'rates'

urlpatterns = [
    path('', views.rates_index, name='index'),
    path('<str:code>/', views.rate_detail, name='detail'),
]
