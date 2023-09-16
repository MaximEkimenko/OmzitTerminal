from django.urls import path
from .views import constructor

urlpatterns = [
    path('', constructor, name='constructor'),
    ]
