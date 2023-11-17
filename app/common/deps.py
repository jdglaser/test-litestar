from dataclasses import dataclass
from inspect import iscoroutinefunction
from typing import Callable, Generic, Optional, TypeVar

import inflection
from litestar.config.app import AppConfig
from litestar.di import Provide
from litestar.plugins import InitPluginProtocol

T = TypeVar("T", bound=Callable)


@dataclass
class Dependency(Generic[T]):
    obj: T
    use_cache: bool


class DependencyRegistry(InitPluginProtocol):
    def __init__(self) -> None:
        self._dep_registry: dict[str, Dependency] = {}

    def on_app_init(self, app_config: AppConfig) -> AppConfig:
        app_config.dependencies.update(self.provide())
        return super().on_app_init(app_config)

    def __call__(self, obj: Optional[T] = None, /, *, use_cache: bool = False, rename: Optional[str] = None) -> T:
        def wrap(obj: T) -> T:
            new_name = inflection.underscore(obj.__name__) if not rename else rename
            if new_name in self._dep_registry:
                raise Exception(f"Dependency '{new_name}' is defined more than once")

            self._dep_registry[new_name] = Dependency(obj, use_cache)
            return obj

        if obj is None:
            return wrap  # type: ignore
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


dep = DependencyRegistry()
