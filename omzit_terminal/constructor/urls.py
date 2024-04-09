from django.urls import path
from .views import constructor, show_instruction

urlpatterns = [
    path('', constructor, name='constructor'),
    path('../scheduler/login/', constructor, name='login'),
    path('instruction/', show_instruction, name='instruction'),
]

