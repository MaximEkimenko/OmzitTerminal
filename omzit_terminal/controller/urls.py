from django.urls import path
from .views import (
    index,
    CreateDefectAct,
    EditDefectAct,
    upload_files
)
app_name = "controller"

urlpatterns = [
    path("", index, name="index"),
    path("create/", CreateDefectAct.as_view(), name="create"),
    path("edit/<int:pk>/", EditDefectAct.as_view(), name="edit"),
    path("upload/<int:pk>/", upload_files, name="upload_files"),

]
