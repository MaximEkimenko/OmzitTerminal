from django.urls import path
from .views import scheduler, schedulerwp, schedulerfio, LoginUser, logout_user

urlpatterns = [
    path('', scheduler, name='scheduler'),
    path('schedulerwp', schedulerwp, name='schedulerwp'),
    path('schedulerfio<int:ws_number>_<str:datetime_done>', schedulerfio, name='schedulerfio'),
    path('login/', LoginUser.as_view(), name='login'),
    path('logout/', logout_user, name='logout'),

    ]
