import datetime
import json
from os import rename
from pprint import pprint
from typing import Any, Mapping, Type, TypeVar

import inflection
import msgspec


class Base(msgspec.Struct, rename="camel", frozen=True):
    ...


class VariantOne(Base, tag=True):
    a: str


class VariantTwo(Base, tag=True):
    a: str
    b: int


class Thing(Base):
    thing_one: int
    ops: list[VariantOne | VariantTwo]


class MyStruct(Base):
    a_cool_thing: str
    a_number: int
    a_bool: bool
    a_list_of_things: list[Thing]


foo = MyStruct(
    a_cool_thing="foo",
    a_number=1,
    a_bool=True,
    a_list_of_things=[Thing(thing_one=1, ops=[VariantOne("one"), VariantTwo("two", 3)])],
)

json_encoded = msgspec.json.encode(foo)
pprint(json.loads(json_encoded))

python_encoded = msgspec.json.decode(json_encoded, type=MyStruct)
print(python_encoded)

print(msgspec.structs.asdict(foo))


class Base2(msgspec.Struct):
    ...


class Test(Base2):
    foo_bar: int
    foo: str


class Outer(Base2):
    inner_test: Test
    dt: datetime.datetime


t = {"inner_test": {"foo_bar": 1, "foo": "hi"}, "dt": "2023-11-18 12:05:23.123"}

T = TypeVar("T", bound=msgspec.Struct)


def from_mapping(obj: Mapping[str, Any], typ: Type[T]) -> T:
    print("S FIELDS", typ.__struct_fields__)
    return msgspec.convert(obj, msgspec.defstruct(typ.__name__, typ.__struct_fields__))  # type: ignore


my_obj = from_mapping(t, Outer)
print(my_obj)
print(msgspec.convert(t, Outer))

# Test2 = msgspec.defstruct("Test2", Test.__struct_fields__)
# print(msgspec.convert(t, Test2))
