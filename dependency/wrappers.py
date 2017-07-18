import typing

import dependency

_default_injector = None


def _get_default_injector() -> dependency.Injector:
    global _default_injector

    if _default_injector is None:
        _default_injector = dependency.Injector()
    return _default_injector


def set_required_state(required_state: typing.Dict[str, type]) -> None:
    injector = _get_default_injector()
    injector.required_state = required_state


def add_provider(func: typing.Callable) -> None:
    injector = _get_default_injector()
    injector.add_provider(func)


def inject(func: typing.Callable) -> dependency.InjectedFunction:
    injector = _get_default_injector()
    return injector.inject(func)
