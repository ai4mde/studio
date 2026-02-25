from typing import Literal, Union, Optional

from pydantic import model_validator
from diagram.models import Node
from metadata.specification.base import RelationBase



class Interface(RelationBase):
    type: Literal["interface"] = "interface"
    provided: str
    required: str
    provided_name: Optional[str] = None
    required_name: Optional[str] = None

    @model_validator(mode='after')
    def fill_interface_names(self):
        ids = [self.provided, self.required]

        nodes = (
            Node.objects.filter(id__in=ids)
            .select_related("cls").only("id", "cls__data")
        )
        name_by_id = {
            str(n.id): (n.cls.data or {}).get("name")
            for n in nodes
        }

        self.provided_name = name_by_id.get(str(self.provided)) or "Unknown provided interface"
        self.required_name = name_by_id.get(str(self.required)) or "Unknown required interface"
        return self

ComponentRelation = Union[Interface]