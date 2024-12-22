from typing import Any
from sqlalchemy.ext.declarative import declared_attr, declarative_base

class CustomBase:
    @declared_attr
    def __tablename__(cls) -> str:
        return cls.__name__.lower()

Base = declarative_base(cls=CustomBase) 