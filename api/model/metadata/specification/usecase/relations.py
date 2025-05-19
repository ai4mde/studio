from typing import Literal

from metadata.specification.base import RelationBase


class UsecaseRelation(RelationBase):
    type: Literal["interaction", "extension", "inclusion"] = "interaction"


__all__ = ["UsecaseRelation"]
