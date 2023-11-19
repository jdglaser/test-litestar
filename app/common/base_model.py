import msgspec


class Base(msgspec.Struct, rename="camel", frozen=True):
    ...
