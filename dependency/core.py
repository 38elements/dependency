import inspect
import typing
from collections import OrderedDict
from contextlib import ExitStack

ParamName = typing.NewType('ParamName', str)

Step = typing.NamedTuple('Step', [
    ('func', typing.Callable),
    ('input_keys', typing.Dict[str, str]),
    ('input_types', typing.Dict[str, type]),
    ('output_key', str),
    ('output_type', type),
    ('param_names', typing.Optional[typing.Dict[str, str]]),
    ('is_context_manager', bool)
])


class InjectedFunction():
    def __init__(self,
                 steps: typing.List[Step],
                 required_state: typing.Dict[str, type]) -> None:
        self.steps = steps
        self.state_key_mapping = {
            key: get_key(value, None, set())
            for key, value in required_state.items()
        }

    def __call__(self, state=None):
        ret = None
        if state is None:
            state = {}
        else:
            state = {
                self.state_key_mapping[key]: value
                for key, value in state.items()
            }

        with ExitStack() as stack:
            for step in self.steps:
                kwargs = {
                    argname: state[state_key]
                    for (argname, state_key) in step.input_keys.items()
                }
                if step.param_names is not None:
                    kwargs.update(step.param_names)
                ret = step.func(**kwargs)
                if step.is_context_manager:
                    stack.enter_context(ret)
                state[step.output_key] = ret
            return ret

    def __repr__(self) -> str:
        indent = 0
        step_reprs = []
        for step in self.steps[:-1]:
            line, indent = self._step_repr(step, indent)
            step_reprs.append(line)
        line, indent = self._step_repr(self.steps[-1], indent, final=True)
        step_reprs.append(line)
        return '\n'.join(step_reprs)

    def _step_repr(self,
                   step: Step,
                   indent: int=0,
                   final: bool=False) -> typing.Tuple[str, int]:
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
    Stores all the state required in order to create
    dependency-injected functions.
    """

    def __init__(self,
                 providers: typing.Dict[type, typing.Callable]=None,
                 required_state: typing.Dict[str, type]=None) -> None:
        if providers is None:
            providers = {}
        if required_state is None:
            required_state = {}

        self.providers = providers
        self.required_state = required_state

    def add_provider(self, func: typing.Callable) -> None:
        sig = inspect.signature(func)
        assert sig.return_annotation is not inspect.Signature.empty
        assert not isinstance(sig.return_annotation, str)
        self.providers[sig.return_annotation] = func

    def inject(self, func: typing.Callable) -> InjectedFunction:
        parameterized_types = set([
            provided_type for provided_type, provider_func
            in self.providers.items()
            if provides_parameterized_type(provider_func)
        ])
        seen_keys = set([
            get_key(cls, None, set())
            for cls in self.required_state.values()
        ])
        steps = create_steps(
            func,
            provided_type=None,
            param_name=None,
            providers=self.providers,
            parameterized_types=parameterized_types,
            seen_keys=seen_keys
        )
        return InjectedFunction(steps, dict(self.required_state))


def is_context_manager(cls: type):
    return hasattr(cls, '__enter__') and hasattr(cls, '__exit__')


def provides_parameterized_type(func: typing.Callable):
    params = inspect.signature(func).parameters.values()
    return any([param.annotation is ParamName for param in params])


def get_key(cls: typing.Union[type, None],
            param_name: typing.Optional[str],
            parameterized_types=typing.Set[type]) -> str:
    """
    Return a unique string name for a class.

    If the class is a dependency that requires its own parameter name as one
    of the inputs then additionally suffix the key with the parameter name.
    """
    if cls is None:
        return ''
    key = cls.__name__.lower()
    if param_name is not None and cls in parameterized_types:
        key += ':' + param_name
    return key


def create_step(func: typing.Callable,
                provided_type: typing.Optional[type],
                param_name: typing.Optional[str],
                parameterized_types: typing.Set[type]) -> Step:
    """
    Return all the information required to run a single step.
    """
    params = inspect.signature(func).parameters.values()

    for param in params:
        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)

    input_keys = OrderedDict([
        (
            param.name,
            get_key(param.annotation, param.name, parameterized_types)
        )
        for param in params
        if param.annotation is not ParamName
    ])
    param_names = {
        param.name: param_name
        for param in params
        if param.annotation is ParamName
    }
    if not param_names:
        param_names = None

    return Step(
        func=func,
        input_keys=input_keys,
        input_types={param.name: param.annotation for param in params},
        output_key=get_key(provided_type, param_name, parameterized_types),
        output_type=provided_type,
        param_names=param_names,
        is_context_manager=is_context_manager(provided_type)
    )


def create_steps(func: typing.Callable,
                 provided_type: typing.Optional[type],
                 param_name: typing.Optional[str],
                 providers: typing.Dict[type, typing.Callable],
                 parameterized_types: typing.Set[type],
                 seen_keys: typing.Set[str]) -> typing.List[Step]:
    """
    Return all the dependant steps required to run the given function.
    """
    seen_keys = set(seen_keys)
    steps = []
    params = inspect.signature(func).parameters.values()

    for param in params:
        key = get_key(param.annotation, param.name, parameterized_types)
        if (key in seen_keys) or (param.annotation is ParamName):
            continue

        assert param.annotation is not inspect.Signature.empty
        assert not isinstance(param.annotation, str)
        assert param.annotation in providers

        provider_func = providers[param.annotation]
        param_steps = create_steps(
            provider_func, param.annotation, param.name, providers,
            parameterized_types, seen_keys
        )
        steps.extend(param_steps)
        seen_keys |= set([
            step.output_key for step in param_steps
        ])

    step = create_step(func, provided_type, param_name, parameterized_types)
    steps.append(step)
    return steps
