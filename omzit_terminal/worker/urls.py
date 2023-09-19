from django.urls import path
from .views import worker, ws_number_choose, draws, make_master_call, show_draw

urlpatterns = [
    path('', ws_number_choose, name='worker_choose'),
    path('<int:ws_number>', worker, name='worker'),
    path('<str:ws_st_number>', draws, name='draws'),
    path(r'<str:ws_st_number>/get', make_master_call),
    path(r'pdf/<int:ws_number>/<str:pdf_file>', show_draw),

    ]
