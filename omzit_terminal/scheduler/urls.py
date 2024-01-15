from django.urls import path
from .views import (scheduler, schedulerwp, schedulerfio, LoginUser, logout_user, td_query, show_workshop_scheme, plan,
                    create_shift_tasks_from_spec, create_specification, confirm_sz_planning,
                    test_scheduler, shift_tasks_reports, shift_tasks_report_view)

# from .views import plan_resort, report # TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО
from constructor.views import show_instruction

urlpatterns = [
    path('', scheduler, name='scheduler'),
    path('schedulerwp', schedulerwp, name='schedulerwp'),
    path('schedulerfio<int:ws_number>_<str:model_order_query>', schedulerfio, name='schedulerfio'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('td_query/', td_query, name='td_query'),
    path('instruction/', show_instruction, name='instruction'),
    path('scheme/', show_workshop_scheme, name='scheme'),
    path('plan/', plan, name='plan'),
    # TODO удалить после тестов
    path('test_scheduler/', test_scheduler, name='test_scheduler'),

    path('st_report_<str:start>_<str:end>/', shift_tasks_reports, name='st_reports'),
    path('view_st_report_<str:start>_<str:end>/', shift_tasks_report_view, name='view_st_report'),
    path('specification/', create_specification, name='specification'),
    path('create_st/', create_shift_tasks_from_spec, name='st_from_spec'),
    path('confirm_sz_planning/', confirm_sz_planning, name='confirm_sz_planning'),
    # path('report<int:workshop>/', report, name='report'), #TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО
    # path('plan_resort/', plan_resort, name='plan_resort'),
]
