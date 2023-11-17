import abc
import logging
from asyncio import iscoroutine
from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import Any, Callable, Generic, Optional, TypeVar

import inflection
from litestar import Litestar, Request, get
from litestar.config.app import AppConfig
from litestar.datastructures import State
from litestar.di import Provide
from litestar.logging import LoggingConfig
from litestar.plugins import InitPluginProtocol
from litestar.types import Scope

T = TypeVar("T", bound=Callable)


@dataclass
class Dependency(Generic[T]):
    obj: T
    use_cache: bool


class DecoratorDepsPlugin(InitPluginProtocol):
    def __init__(self) -> None:
        self._dep_registry: dict[str, Dependency] = {}

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.dependencies.update(self.provide())
        return super().on_app_init(app_config)

    def __call__(self, obj: Optional[T] = None, /, *, use_cache: bool = False, rename: Optional[str] = None) -> Any:
        def wrap(obj: T) -> T:
            new_name = inflection.underscore(obj.__name__) if not rename else rename
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


dependency = DecoratorDepsPlugin()


@dependency(use_cache=True)
class SomeDep:
    def __init__(self, my_dep: str) -> None:
        print("HERE init")
        print(my_dep)
        self.my_dep = my_dep
        print("Done initing SomeDep")

    async def get_my_dep(self) -> str:
        print("IN get_my_dep")
        return self.my_dep


@dependency
async def my_dep(state: State) -> str:
    return state.my_dep


@get("/")
async def test_dep(some_dep: SomeDep) -> dict:
    print("In handler")
    return {"dep": await some_dep.get_my_dep()}


async def log_exception(exception: Exception, scope: Scope) -> None:
    request: Request = Request(scope)
    request.logger.exception(str(exception))


def startup(app: Litestar) -> None:
    app.state.my_dep = "my dep from startup!"


log_config = LoggingConfig(
    root={"level": logging.getLevelName(logging.DEBUG), "handlers": ["console"]},
)


app = Litestar(
    route_handlers=[test_dep],
    after_exception=[log_exception],
    logging_config=log_config,
    on_startup=[startup],
    plugins=[dependency],
)
