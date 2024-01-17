from metadata.api import metadata_router
from django.urls import path
from ninja import NinjaAPI

api = NinjaAPI(
    title="AI4MDE Studio",
    version="1.0.0",
    description="AI4MDE Studio API"
)
api.add_router('/metadata/', metadata_router)

urlpatterns = [
    path('api/v1/', api.urls)
]
