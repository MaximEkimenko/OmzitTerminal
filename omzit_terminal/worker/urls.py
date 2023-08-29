from django.urls import path
from .views import worker, ws_number_choose

urlpatterns = [
    path('', ws_number_choose, name='worker_choose'),
    path('<int:ws_number>', worker, name='worker'),
    ]
