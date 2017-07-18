# Dependency

*A dependency injection library, using Python type annotations.*

[![Build Status](https://travis-ci.org/encode/dependency.svg?branch=master)](https://travis-ci.org/encode/dependency)
[![codecov](https://codecov.io/gh/encode/dependency/branch/master/graph/badge.svg)](https://codecov.io/gh/encode/dependency)
[![Package version](https://badge.fury.io/py/dependency.svg)](https://pypi.python.org/pypi/dependency)

**Requirements**: Python 3.5+

---

Dependency Injection is a pattern that can help with managing complexity
and testability in large codebases.

The `dependency` package provides the building blocks required to
implement type-annotation based dependency injection.

## Examples

Rather than starting with the API of the package itself, let's instead take
a look at the sort of code the `dependency` package allows you to write.

### Web framework

In this case we've built a web framework that supports dependency injected components
to provide the information that each view uses:

```python
from web_framework import Method, Path, Headers, App, Response
import json


def echo_request_info(method: Method, path: Path, headers: Headers):
    content = json.dumps({
        'method': method,
        'path': path,
        'headers': dict(headers)
    }, indent=4).encode('utf-8')
    return Response(content)


def echo_user_agent(user_agent: Header):
    content = json.dumps({
        'User-Agent': user_agent
    }, indent=4).encode('utf-8')
    return Response(content)


app = App({
    '/request/': echo_request_info,
    '/user-agent/': echo_user_agent
})


if __name__ == '__main__':
    app.run()
```

You can see that the views have more expressive interfaces and are more easily
testable than they would be if every function accepted a single `request` argument.

The framework source code is available here: [/examples/web_framework.py](/examples/web_framework.py)

### Test framework

Here's another example, of using `dependency` to create a testing framework
that supports dependency-injection of reusable components into test cases...

```python
from tempfile import TemporaryDirectory
from examples.test_framework import run_tests
import dependency
import os


@dependency.add_provider
def get_temp_dir() -> TemporaryDirectory:
    """
    A temporary directory component that may be injected into test cases.
    Each directory will only exist for the lifetime of a single test.
    """
    return TemporaryDirectory()


def test_list_empty_directory(tmp_dir: TemporaryDirectory):
    assert len(os.listdir(tmp_dir.name)) == 0


def test_list_nonempty_directory(tmp_dir: TemporaryDirectory):
    path = os.path.join(tmp_dir.name, 'example.txt')
    open(path, 'w').close()
    assert len(os.listdir(tmp_dir.name)) == 1


if __name__ == "__main__":
    run_tests()
```

The framework source code is available here: [/examples/test_framework.py](/examples/test_framework.py)

---

## Library usage

The core functionality is provided as two functions:

* `dependency.add_provider(func: Callable)` - Add a provider function.
* `dependency.inject(func: Callable)` - Create a dependency injected function.

You can use these either as plain function calls, or as decorators...

```python
import datetime
import dependency
import typing

Now = typing.NewType('Now', datetime.datetime)

@dependency.add_provider
def get_now() -> Now:
    datetime.datetime.now()

@dependency.inject
def do_something(now: Now):
    ...

do_something()
```

The functions passed to `dependency.add_provider()` must be fully type annotated.
The parameters of a provider function may include class dependencies themselves.

### Working with initial state

Often you'll want your provider functions to depend on some initial state.
This might be something that's setup when your application is initialised,
or state that exists in the context of a single HTTP request/response cycle.

* `dependency.set_required_state(required_state: Dict[str, type])`

You can include required state classes in provider functions...

```python
import dependency

# Add some provider functions
@dependency.add_provider
def get_database_session(engine: Engine) -> Session:
    """
    Return a database session, given the database engine.
    """

@dependency.add_provider
def create_database_engine(settings: settings) -> Engine:
    """
    Return a database engine instance, given the application settings.
    """

@dependency.add_provider
def get_request(environ: Environ) -> Request:
    """
    Return a request instance, given a WSGI environ.
    """

# Indicate classes that will be provided as initial state
dependency.set_required_state({'settings': Settings, 'environ': Environ})

# Wrap a function in a dependency injection
@dependency.inject
def list_users(request: Request, session: Session):
    ...
```

In order to run a dependency that has some required initial state, you'll
need to include the state as a keyword argument.

```python
list_users(state={'settings': ..., 'environ': ...})
```

### Namespaced dependencies

The function calls we've looked at so far all operate against a single
global dependency namespace, but you can also create individual instances
giving you more explicit control over the dependency injection.

```python
injector = dependency.Injector()

@injector.add_provider
def get_now() -> Now:
    datetime.datetime.now()

@injector.inject
def do_something(now: Now):
    ...
```

The constructor takes two arguments, both of which are optional:

* `providers: Dict[type, Callable]` - A map of dependency types onto their provider functions.
* `required_state: Dict[str, type]` - A map of any dependency types which will be provided as initial state.

These are also both available directly on the instance...

```python
injector = dependency.Injector()
injector.providers[Now] = get_now
```
