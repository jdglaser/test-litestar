from typing import Mapping, Type, TypeVar

import msgspec
from inflection import camelize
from sqlalchemy import RowMapping

T = TypeVar("T", bound=msgspec.Struct)


def from_mapping(obj: Mapping, typ: Type[T]) -> T:
    return msgspec.convert(obj, msgspec.defstruct(typ.__name__, typ.__struct_fields__))  # type: ignore


def camelize_row_mapping(row_mapping: RowMapping) -> dict:
    return {camelize(k, False): v for k, v in row_mapping.items()}
