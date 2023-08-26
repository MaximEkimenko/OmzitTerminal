from django.urls import path
from .views import scheduler, schedulerwp

urlpatterns = [
    path('', scheduler, name='scheduler'),
    path('schedulerwp', schedulerwp, name='schedulerwp'),
    ]
