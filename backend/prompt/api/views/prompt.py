from ninja import Router

prompt = Router()

prompt.get("/")
def prompt_root(request):
    return {"message": "Hello World"}

__all__ = ["prompt"]
