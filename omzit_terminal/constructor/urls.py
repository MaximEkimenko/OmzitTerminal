from django.urls import path
from .views import constructor, draw_folder_redirect, show_instruction

urlpatterns = [
    path('', constructor, name='constructor'),
    path('../scheduler/login/', constructor, name='login'),
    path('draw_folder_redirect/', draw_folder_redirect, name='draw_folder_redirect'),
    path('instruction/', show_instruction, name='instruction'),
]
