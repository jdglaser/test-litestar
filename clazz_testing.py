class Foo:
    def __init__(self, a: str) -> None:
        self.a = a

    def shutdown(self) -> None:
        self.a = "b"


foo = Foo(a="a")

d = {"foo": foo}

print(d["foo"].a)

a = d["foo"]
a.shutdown()

print(d["foo"].a)
