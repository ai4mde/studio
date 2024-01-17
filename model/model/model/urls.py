from django.urls import path
from model.api import api

urlpatterns = [
    path('api/v1/', api.urls)
]
