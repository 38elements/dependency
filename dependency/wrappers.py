import dependency
import inspect
import typing


_default_injector = None


def _get_default_injector() -> dependency.Injector:
    global _default_injector

    if _default_injector is None:
        _default_injector = dependency.Injector()
    return _default_injector


def set_required_state(required_state: typing.Dict[str, type]) -> None:
    injector = _get_default_injector()
    injector.required_state = required_state


def provider(func: typing.Callable) -> None:
    injector = _get_default_injector()

    sig = inspect.signature(func)

    params = sig.parameters.values()
    for param in params:
        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)

    assert sig.return_annotation is not inspect.Signature.empty
    assert not isinstance(sig.return_annotation, str)
    injector.providers[sig.return_annotation] = func


def inject(func: typing.Callable) -> dependency.InjectedFunction:
    injector = _get_default_injector()
    return injector.inject(func)
