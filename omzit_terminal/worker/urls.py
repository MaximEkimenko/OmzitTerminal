from django.urls import path
from .views import worker, ws_number_choose, draws, make_master_call, show_draw, make_dispatcher_call

urlpatterns = [
    path('', ws_number_choose, name='worker_choose'),
    path('<int:ws_number>', worker, name='worker'),
    path('<str:ws_st_number>', draws, name='draws'),
    path(r'<str:ws_st_number>/get_master', make_master_call, name='master_call'),
    path(r'<str:ws_st_number>/get_dispatcher', make_dispatcher_call, name='dispatcher_call'),
    path(r'pdf/<int:ws_number>/<str:pdf_file>', show_draw),

]
