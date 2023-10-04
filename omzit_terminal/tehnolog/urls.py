from django.urls import path
from .views import tehnolog_wp, new_model_query, send_draw_back

urlpatterns = [
    path('', tehnolog_wp, name='tehnolog'),
    path('new_model_query', new_model_query, name='new_model_query'),
    path('send_draw_back', send_draw_back, name='send_draw_back'),
]

