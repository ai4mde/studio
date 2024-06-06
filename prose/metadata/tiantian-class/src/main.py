import uuid
from fastapi import FastAPI
from .nlp import generate_uml
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

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
        "message": "Send a POST-request to / with the requirements in body"
    }

class RunNLP(BaseModel):
    requirements: str

@app.get("/run_nlp/")
def run_nlp(requirements: str):
    res = generate_uml(requirements)
    classes = res[0].items()
    relations = res[1]

    _cls_out = {}
    _rel_out = {}

    for cls, val in classes:
        _cls_out[cls] = {
            'id': uuid.uuid4(),
            'data': {
                'name': cls
            }
        }

    for rel in relations:
        if (_cls_out.get(rel[1][1]) and _cls_out.get(rel[2][1])):
            id = uuid.uuid4()
            _rel_out[id] = {
                'id': id,
                'data': {
                    'type': rel[0][0],
                    'source': _cls_out[rel[1][1]].get('id'),
                    'target': _cls_out[rel[2][1]].get('id'),
                    'label': rel[0][1],
                }
            }

    return {
        'classifiers': _cls_out.values(),
        'relations': _rel_out.values(),
    }
