from django.urls import path
from .views import tehnolog_wp

urlpatterns = [
    path('', tehnolog_wp, name='tehnolog'),
    ]
