from metadata.api import metadata_router
from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI()
api.add_router('/metadata/', metadata_router)

urlpatterns = [
    path('api/v1/', api)
]
