from django.contrib import admin
from django.urls import path, include
from .views import home

urlpatterns = [
    path('admin/', admin.site.urls, name='admin'),
    path('', home, name='home'),
    path('tehnolog/', include('tehnolog.urls')),
    path('scheduler/', include('scheduler.urls')),
    path('worker/', include('worker.urls')),
]

# TODO написать обработчики ошибок 404, 500, перед деплоем и debug False
# handler404 = page_not_found




