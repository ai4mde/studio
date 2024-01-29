from pydantic.fields import Field
from pydantic.root_model import BaseModel
from pydantic.types import Annotated, Union
from .activity import ActivityClassifier, ActivityRelation
from .classes import ClassClassifier, ClassRelation
from .usecase import UsecaseClassifier, UsecaseRelation

Classifier = Annotated[
    Union[
        ActivityClassifier,
        ClassClassifier,
        UsecaseClassifier,
    ],
    Field(
        discriminator="diagram",
    )
]

Relation = Annotated[
    Union[
        ActivityRelation,
        ClassRelation,
        UsecaseRelation,
    ],
    Field(
        discriminator="diagram",
    ),
]

__all__ = [ "Classifier", "Relation" ]
