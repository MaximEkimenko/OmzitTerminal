from django.urls import path
from .views import (
    index,
    CreateDefectAct

)
app_name = "controller"

urlpatterns = [
    path("", index, name="index"),
    path("create", CreateDefectAct.as_view(), name="create"),

]
