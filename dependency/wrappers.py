import dependency
import inspect


_default_injector = None


def get_default_injector():
    global _default_injector

    if _default_injector is None:
        _default_injector = dependency.Injector({})
    return _default_injector


def set_required_state(state):
    injector = get_default_injector()
    injector.set_required_state(state)


def provider(func):
    injector = get_default_injector()

    sig = inspect.signature(func)

    params = sig.parameters.values()
    for param in params:
        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)

    assert sig.return_annotation is not inspect.Signature.empty
    assert not isinstance(sig.return_annotation, str)
    injector.providers[sig.return_annotation] = func


def inject(func):
    injector = get_default_injector()
    return injector.inject(func)
