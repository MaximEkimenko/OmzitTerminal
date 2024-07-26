from django.urls import path

from api.views import (ShiftTaskListView, StartJobView, CallMaserView, CallDispatcherView, # noqa
                       save_strat_plan, delete_model_from_start_plan)  # noqa

app_name = "api"

urlpatterns = [
    # auth
    path("worker/<int:ws_number>", ShiftTaskListView.as_view(), name="api-worker"),
    path("start-job", StartJobView.as_view(), name="start-job"),
    path("call-master", CallMaserView.as_view(), name="call-master"),
    path("call-dispatcher", CallDispatcherView.as_view(), name="call-dispatcher"),
    path('save_strat', save_strat_plan, name='save_strat_plan'),
    path('delete_model<int:model_id>', delete_model_from_start_plan, name='delete_model_from_start_plan'),
]
