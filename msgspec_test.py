import json
from pprint import pprint

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
