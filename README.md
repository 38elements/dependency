# dependency

*A dependency injection library, using Python type annotations.*

Dependency Injection is a pattern that can help with managing complexity
and testability in large codebases.

The `dependency` package provides the building blocks required to
implement type-annotation based dependency injection.

## Web framework

Let's take a look at the sort of code the `dependency` package allows you to write.

In this case we've got a web framework that supports dependency injected components
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

You can see that the views have more expressive interfaces and are more
easily testable, than if every function accepted a single `request` argument.

The framework source code is available here: [/examples/web_framework.py](/examples/web_framework.py)

The `dependency` package supports context managers, so you could also provide
components such as a `Session` that automatically handles commit/rollback
depending on if a view returns normally or raises an exception.

## Test framework

Here's another example, of using `dependency` to create a testing framework
that supports dependency-injection of reusable components into test cases...

```python
from tempfile import TemporaryDirectory
from examples.test_framework import run_tests
import dependency
import os


@dependency.provider
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
