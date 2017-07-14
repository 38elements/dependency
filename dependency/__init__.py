from contextlib import ExitStack
import inspect
import tempfile
import typing
import functools


__version__ = '0.0.1'


Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_types', typing.Dict[str, typing.Type]),
    ('output_key', str),
    ('output_type', typing.Type),
    ('is_context_manager', bool)
])


class Pipeline():
    def __init__(self, steps: typing.List[Step], initial_state: typing.Dict[str, type]):
        self.steps = steps
        self.kwarg_to_state_key = {
            key: get_key(value)
            for key, value in initial_state.items()
        }

    def __call__(self, **kwargs):
        ret = None
        state = {
            self.kwarg_to_state_key[key]: value
            for key, value in kwargs.items()
        }

        with ExitStack() as stack:
            for step in self.steps:
                kwargs = {
                    argname: state[state_key]
                    for (argname, state_key) in step.input_keys.items()
                }
                ret = step.func(**kwargs)
                if step.is_context_manager:
                    stack.enter_context(ret)
                state[step.output_key] = ret
            return ret


_providers = {}


def provider(func: typing.Callable) -> None:
    """
    Add the given function to the available provider functions.
    """
    global _providers

    sig = inspect.signature(func)

    assert sig.return_annotation is not inspect.Signature.empty
    assert not isinstance(sig.return_annotation, str)
    _providers[sig.return_annotation] = func


def is_context_manager(obj):
    return hasattr(obj, '__enter__') and hasattr(obj, '__exit__')


def get_key(cls: typing.Union[typing.Type, None]) -> str:
    """
    Return a unique string name for a class.
    """
    if cls is None:
        return ''
    return '%s:%d' % (cls.__name__, id(cls))


def create_step(func: typing.Callable) -> Step:
    """
    Return all the information required to run a function as a single step in a pipeline.
    """
    sig = inspect.signature(func)
    params = sig.parameters.values()

    return_type = sig.return_annotation
    assert not isinstance(return_type, str)
    if return_type is inspect.Signature.empty:
        return_type = None

    for param in params:
        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)

    return Step(
        func=func,
        input_keys={param.name: get_key(param.annotation) for param in params},
        input_types={param.name: param.annotation for param in params},
        output_key=get_key(return_type),
        output_type=return_type,
        is_context_manager=is_context_manager(sig.return_annotation)
    )


def create_steps(func: typing.Callable, providers: typing.Dict[str, typing.Callable], seen_types: typing.Set[type]) -> typing.List[Step]:
    seen_types = set(seen_types)
    steps = []
    sig = inspect.signature(func)

    for param in sig.parameters.values():
        if param.annotation in seen_types:
            continue

        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)
        assert param.annotation in _providers

        provider_func = providers[param.annotation]
        param_steps = create_steps(provider_func, providers, seen_types)
        steps.extend(param_steps)
        seen_types |= set([step.output_type for step in param_steps])

    step = create_step(func)
    steps.append(step)
    return steps


def inject(func: typing.Callable, initial_state: typing.Dict[str, type]=None) -> Pipeline:
    global _providers

    if initial_state is None:
        initial_state = {}
    seen_types = set(initial_state.values())
    steps = create_steps(func, _providers, seen_types)
    return Pipeline(steps, initial_state)
