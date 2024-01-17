from django.http import HttpResponse
from ninja import NinjaAPI
from metadata.api import metadata_router
from model.auth import auth, create_token

api = NinjaAPI(
    title="AI4MDE Studio",
    version="1.0.0",
    description="AI4MDE Studio API",
    auth=auth,
    csrf=True,
)
api.add_router('/metadata/', metadata_router)

@api.post('/auth/token', auth=None, tags=['authentication'])
def get_token(request, username: str, password: str, response: HttpResponse):
    token = create_token(username, password)
    if token:
        response.set_cookie(
            'key',
            token,
            httponly=True
        )
        return {'token': token}
    return 403, {"message": "User not found."}