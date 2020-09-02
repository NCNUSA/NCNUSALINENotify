from django.contrib import admin
from django.urls import path
from api.views import Send, index, register

urlpatterns = [
    path('admin/', admin.site.urls),
    path('pushMessage', Send.as_view()),
    path('', index),
    path('register', register),
]
