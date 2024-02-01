from django.urls import path
from .views import tehnolog_wp, new_model_query, send_draw_back, plasma_tehnolog_distribution, plasma_tehnolog, \
    get_orders_models, shift_task_from_tech_data, set_shift_task_status, get_order_model_shift_tasks

urlpatterns = [
    path('', tehnolog_wp, name='tehnolog'),
    path('new_model_query', new_model_query, name='new_model_query'),
    path('send_draw_back', send_draw_back, name='send_draw_back'),
    path('plasma_tehnolog_distribution', plasma_tehnolog_distribution, name='plasma_tehnolog_distribution'),
    path('plasma_tehnolog', plasma_tehnolog, name='plasma_tehnolog'),
    path('tech_data', shift_task_from_tech_data, name='tech_data'),
    path('orders_models', get_orders_models, name='orders_models'),
    path('change_st_status', set_shift_task_status, name='change_st_status'),
    path('shift_tasks/<str:order_model>', get_order_model_shift_tasks, name='shift_tasks'),
]

