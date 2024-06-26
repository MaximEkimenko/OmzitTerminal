from django.urls import path
from .views import (
    CreateDefectAct,
    EditDefectAct,
    upload_files,
    file_list,
    show_file,
    delete_file_proc,
    defect_report,
    DefectsView,
    DefectCard,
)
app_name = "controller"

urlpatterns = [
    # path("", index, name="index"),
    path("", DefectsView.as_view(), name="index"),
    path("create/", CreateDefectAct.as_view(), name="create"),
    path("edit/<int:pk>/", EditDefectAct.as_view(), name="edit"),
    path("upload/<int:pk>/", upload_files, name="upload_files"),
    path("filelist/<int:pk>/", file_list, name="file_list"),
    path("show_file/<path:path>/", show_file, name="show_file"),
    path("del_file/<int:pk>/<path:path>/", delete_file_proc, name="delete_file_proc"),
    path("report/", defect_report, name="defect_report"),
    path("card/<int:pk>/", DefectCard.as_view(), name="defect_card"),

]
