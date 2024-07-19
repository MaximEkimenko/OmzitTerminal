from django.urls import path
from .views import (scheduler, schedulerwp, schedulerfio, LoginUser, logout_user, td_query, show_workshop_scheme, plan,
                    shift_tasks_reports, shift_tasks_report_view, strat_plan)

# from .views import plan_resort, report # TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО
from constructor.views import show_instruction

# TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
# from .views import create_shift_tasks_from_spec, create_specification, test_scheduler

urlpatterns = [
    path('', scheduler, name='scheduler'),
    path('schedulerwp', schedulerwp, name='schedulerwp'),
    path('schedulerfio<int:ws_number>_<str:model_order_query>', schedulerfio, name='schedulerfio'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),
    path('td_query/', td_query, name='td_query'),
    path('instruction/', show_instruction, name='instruction'),
    path('scheme/', show_workshop_scheme, name='scheme'),
    path('strat_plan<int:workshop>/', strat_plan, name='strat_plan'),
    path('st_report_<str:start>_<str:end>/', shift_tasks_reports, name='st_reports'),
    path('view_st_report_<str:start>_<str:end>/', shift_tasks_report_view, name='view_st_report'),


    # TODO ФУНКЦИОНАЛ ОТЧЁТОВ ЗАКОНСЕРВИРОВАНО
    # path('confirm_sz_planning/', confirm_sz_planning, name='confirm_sz_planning'),
    # path('report<int:workshop>/', report, name='report'),
    # path('plan_resort/', plan_resort, name='plan_resort'),

    # TODO ФУНКЦИОНАЛ ЗАЯВИТЕЛЯ ПЛАЗМЫ И НОВОГО РАБОЧЕГО МЕСТА ТЕХНОЛОГА законсервировано
    # path('test_scheduler/', test_scheduler, name='test_scheduler'),
    # path('specification/', create_specification, name='specification'),
    # path('create_st/', create_shift_tasks_from_spec, name='st_from_spec'),
]
