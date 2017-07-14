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
