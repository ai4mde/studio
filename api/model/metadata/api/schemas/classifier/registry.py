from metadata.models.types import ClassifierType

from .activity_diagram import ACTIVITY_DIAGRAM_SCHEMAS
from .class_diagram import CLASS_DIAGRAM_SCHEMAS
from .common import EMPTY_CLASSIFIER_SCHEMAS
from .component_diagram import COMPONENT_DIAGRAM_SCHEMAS
from .usecase_diagram import USECASE_DIAGRAM_SCHEMAS


CLASSIFIER_SCHEMAS = {
    **ACTIVITY_DIAGRAM_SCHEMAS,
    **CLASS_DIAGRAM_SCHEMAS,
    **COMPONENT_DIAGRAM_SCHEMAS,
    **USECASE_DIAGRAM_SCHEMAS,
}

def get_classifier_schemas(classifier_type: ClassifierType):
    return CLASSIFIER_SCHEMAS.get(
        classifier_type,
        EMPTY_CLASSIFIER_SCHEMAS
    )
