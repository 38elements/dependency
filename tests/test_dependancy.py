import dependency


class User():
    def __init__(self, username):
        self.username = username


def user_func(u: User):
    return u


def test_dependency():
    @dependency.provider
    def mock_user() -> User:
        return User('example')

    func = dependency.inject(user_func)
    u = func()
    assert isinstance(u, User)
    assert u.username == 'example'



events = []


class DatabaseSession():
    def __init__(self, config):
        self.config = config

    def __enter__(self):
        global events
        events.append('setup')

    def __exit__(self, *args, **kwargs):
        global events
        events.append('teardown')


def db_func(session: DatabaseSession):
    pass


def test_context_manager():
    @dependency.provider
    def mock_database() -> DatabaseSession:
        return DatabaseSession({})

    func = dependency.inject(db_func)
    func()
    assert events == ['setup', 'teardown']


def test_pipelines():
    class Environ(dict):
        pass

    class Method(str):
        pass

    class Headers(dict):
        pass

    @dependency.provider
    def get_method(environ: Environ) -> Method:
        return Method(environ['METHOD'])

    @dependency.provider
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

    func = dependency.inject(echo_method_and_headers, initial_state={'environ': Environ})
    func(environ={'METHOD': 'GET', 'CONTENT_TYPE': 'application/json', 'HTTP_HOST': '127.0.0.1'})
