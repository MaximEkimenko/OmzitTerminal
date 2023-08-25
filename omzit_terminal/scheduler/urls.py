from django.urls import path
from .views import scheduler

urlpatterns = [
    path('', scheduler, name='scheduler'),
    ]
