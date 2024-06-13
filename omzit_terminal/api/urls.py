from django.urls import path

from api.views import ShiftTaskListView, StartJobView, CallMaserView, CallDispatcherView, save, index

app_name = "api"

urlpatterns = [
    # auth
    path("worker/<int:ws_number>", ShiftTaskListView.as_view(), name="api-worker"),
    path("start-job", StartJobView.as_view(), name="start-job"),
    path("call-master", CallMaserView.as_view(), name="call-master"),
    path("call-dispatcher", CallDispatcherView.as_view(), name="call-dispatcher"),
    path('save/', save, name='save'),
    path('', index, name='index')
]
