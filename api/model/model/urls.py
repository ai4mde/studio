from django.contrib import admin
from django.urls import path
from model.api import api

urlpatterns = [
    path("api/v1/", api.urls),
    path("admin/", admin.site.urls),
]
