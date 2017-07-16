import dependency


def test_injection():
    class Environ(dict):
        pass

    class Method(str):
        pass

    class Headers(dict):
        pass

    def get_method(environ: Environ) -> Method:
        return Method(environ['METHOD'])

    def get_headers(environ: Environ) -> Headers:
        headers = {}
        for key, value in environ.items():
            if key.startswith('HTTP_'):
                key = key[5:].replace('_', '-').lower()
                headers[key] = value
            elif key in ('CONTENT_TYPE', 'CONTENT_LENGTH'):
                key = key.replace('_', '-').lower()
                headers[key] = value
        return Headers(headers)

    def echo_method_and_headers(method: Method, headers: Headers):
        return {'method': method, 'headers': headers}

    injector = dependency.Injector(
        providers={
            Method: get_method,
            Headers: get_headers
        },
        state={
            'environ': Environ
        }
    )

    func = injector.inject(echo_method_and_headers)
    assert [
        step.func for step in func.steps
    ] == [
        get_method,
        get_headers,
        echo_method_and_headers
    ]

    environ = {
        'METHOD': 'GET',
        'CONTENT_TYPE': 'application/json',
        'HTTP_HOST': '127.0.0.1'
    }
    result = func(environ=environ)
    assert result == {
        'method': 'GET',
        'headers': {'content-type': 'application/json', 'host': '127.0.0.1'}
    }
    assert repr(func) == '\n'.join([
        'method = get_method(environ=environ)',
        'headers = get_headers(environ=environ)',
        'return echo_method_and_headers(method=method, headers=headers)'
    ])


def test_context_manager():
    class Session():
        events = []

        def __init__(self):
            pass

        def __enter__(self):
            self.events.append('__enter__')

        def __exit__(self, *args, **kwargs):
            self.events.append('__exit__')

    injector = dependency.Injector(providers={
        Session: Session,
    })

    def do_something(session: Session):
        pass

    func = injector.inject(do_something)
    func()

    assert Session.events == ['__enter__', '__exit__']
    assert repr(func) == '\n'.join([
        'with Session() as session:',
        '    return do_something(session=session)'
    ])
