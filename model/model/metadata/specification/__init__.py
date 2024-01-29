from typing import Annotated, Union
from pydantic.fields import Field
from .activity import ActivityClassifier, ActivityRelation
from .classes import ClassClassifier, ClassRelation
from .usecase import UsecaseClassifier, UsecaseRelation

Classifier = Annotated[
    Union[
        ActivityClassifier,
        ClassClassifier,
        UsecaseClassifier,
    ],
    Field(discriminator="type"),
]

Relation = Annotated[
    Union[
        ActivityRelation,
        ClassRelation,
        UsecaseRelation,
    ],
    Field(discriminator="type"),
]

__all__ = ["Classifier", "Relation"]
