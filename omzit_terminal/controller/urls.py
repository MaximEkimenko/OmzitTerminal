from django.urls import path
from .views import (
    index,
    CreateDefectAct,
    EditDefectAct,

)
app_name = "controller"

urlpatterns = [
    path("", index, name="index"),
    path("create/", CreateDefectAct.as_view(), name="create"),
    path("edit/<int:pk>/", EditDefectAct.as_view(), name="edit"),

]
