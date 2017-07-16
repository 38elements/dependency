from contextlib import ExitStack
import inspect
import tempfile
import typing
import functools


Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_types', typing.Dict[str, typing.Type]),
    ('output_key', str),
    ('output_type', typing.Type),
    ('is_context_manager', bool)
])


class InjectedFunction():
    def __init__(self, steps: typing.List[Step], required_state: typing.Dict[str, type]):
        self.steps = steps
        self.kwarg_to_state_key = {
            key: get_key(value)
            for key, value in required_state.items()
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

    def __repr__(self):
        indent = 0
        step_reprs = []
        for step in self.steps[:-1]:
            line, indent = self._step_repr(step, indent)
            step_reprs.append(line)
        line, indent = self._step_repr(self.steps[-1], indent, final=True)
        step_reprs.append(line)
        return '\n'.join(step_reprs)

    def _step_repr(self, step, indent=0, final=False):
        params = ', '.join([
            '%s=%s' % (argname, state_key)
            for argname, state_key in step.input_keys.items()
        ])
        func_name = step.func.__name__
        var_name = step.output_key

        line = '    ' * indent
        if final:
            line += 'return %s(%s)' % (func_name, params)
        elif step.is_context_manager:
            line += 'with %s(%s) as %s:' % (func_name, params, var_name)
            indent += 1
        else:
            line += '%s = %s(%s)' % (var_name, func_name, params)
        return (line, indent)


class Injector():
    """
    Stores all the state determining how to create dependency injected functions.
    """

    def __init__(self, providers: typing.Dict[str, typing.Callable], state: typing.Dict[str, type]=None):
        if state is None:
            state = {}

        self.providers = providers
        self.state = state
        self.seen_types = set(state.values())

    def required_state(self, state=None):
        if state is None:
            state = {}
        self.state = state
        self.seen_types = set(state.values())

    def inject(self, func: typing.Callable) -> InjectedFunction:
        steps = create_steps(func, None, self.providers, self.seen_types)
        return InjectedFunction(steps, dict(self.state))


def is_context_manager(obj):
    return hasattr(obj, '__enter__') and hasattr(obj, '__exit__')


def get_key(cls: typing.Union[typing.Type, None]) -> str:
    """
    Return a unique string name for a class.
    """
    if cls is None:
        return ''
    return '%s' % cls.__name__.lower()


def create_step(func: typing.Callable, provided_type: type) -> Step:
    """
    Return all the information required to run a single step.
    """
    params = inspect.signature(func).parameters.values()

    for param in params:
        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)

    return Step(
        func=func,
        input_keys={param.name: get_key(param.annotation) for param in params},
        input_types={param.name: param.annotation for param in params},
        output_key=get_key(provided_type),
        output_type=provided_type,
        is_context_manager=is_context_manager(provided_type)
    )


def create_steps(func: typing.Callable, provided_type: type, providers: typing.Dict[str, typing.Callable], seen_types: typing.Set[type]) -> typing.List[Step]:
    """
    Return all the dependant steps required to run the given function.
    """
    seen_types = set(seen_types)
    steps = []
    params = inspect.signature(func).parameters.values()

    for param in params:
        if param.annotation in seen_types:
            continue

        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)
        assert param.annotation in providers

        provider_func = providers[param.annotation]
        param_steps = create_steps(provider_func, param.annotation, providers, seen_types)
        steps.extend(param_steps)
        seen_types |= set([step.output_type for step in param_steps])

    step = create_step(func, provided_type)
    steps.append(step)
    return steps
