from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {
        "message": "Send a POST-request to / with the project name and runtime json in body"
    }


class CreateProjectContainer(BaseModel):
    runtime: Any
    project: str


@app.post("/")
def create_project_container(request, data: CreateProjectContainer):
    return {"status": "ok"}
