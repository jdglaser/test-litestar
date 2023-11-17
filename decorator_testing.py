from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import Any, Callable, Generic, Optional, TypeVar

import inflection
from litestar.di import Provide

T = TypeVar("T", bound=Callable)


@dataclass
class Dependency(Generic[T]):
    obj: T
    use_cache: bool


class Dep:
    def __init__(self) -> None:
        self._dep_registry: dict[str, Dependency] = {}

    def __call__(self, obj: Optional[T] = None, /, *, use_cache: bool = False) -> Any:
        def wrap(obj: T) -> T:
            new_name = inflection.underscore(obj.__name__)
            if new_name in self._dep_registry:
                raise Exception(f"Dependency '{new_name}' is defined more than once")

            self._dep_registry[new_name] = Dependency(obj, use_cache)
            return obj

        if obj is None:
            return wrap
        else:
            return wrap(obj)

    def provide(self) -> dict[str, Provide]:
        provide_dict: dict[str, Provide] = {}
        for k, v in self._dep_registry.items():
            if iscoroutinefunction(v.obj):
                provide_dict[k] = Provide(v.obj, use_cache=v.use_cache)
            else:
                provide_dict[k] = Provide(v.obj, sync_to_thread=False, use_cache=v.use_cache)
        return provide_dict


dep = Dep()


@dep(use_cache=False)
class Foo:
    def __init__(self) -> None:
        print("Hello!")


@dep
class Bar:
    def __init__(self) -> None:
        print("Hello from Bar")


@dep
async def my_func() -> str:
    return "f"


@dep(use_cache=True)
async def my_func2() -> int:
    return 1


print(dep.provide())
