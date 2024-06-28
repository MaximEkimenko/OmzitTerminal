from django.contrib import admin
from django.urls import path, include
from django.views.i18n import JavaScriptCatalog
from tst_in_terminal import tst

from .views import home

urlpatterns = [
    path("admin/", admin.site.urls, name="admin"),
    path("", home, name="home"),
    path("tehnolog/", include("tehnolog.urls")),
    path("scheduler/", include("scheduler.urls")),
    path("worker/", include("worker.urls")),
    path("constructor/", include("constructor.urls")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
    path("api/", include("api.urls")),
    path("api-auth/", include("rest_framework.urls")),
    path("orders/", include("orders.urls")),
    path("tst/", tst, name="tst"),
]

# TODO написать обработчики ошибок 404, 500, перед деплоем и сделать debug False
# handler404 = page_not_found
