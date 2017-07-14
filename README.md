# dependency

*A dependency injection library, using Python type annotations.*


```python
def signup(request: Request, email_backend: EmailBackend):
    text = WELCOME_TEMPLATE.format(username=user.username)
    sent_ok = email_backend.send(to=user.email, text=text)
    return sent_ok
```


```
import dependency


@dependency.provider
def create_mock_user() -> User:
    return User('example')


@dependency.provider
def create_mock_email() -> EmailBackend:
    return MockEmailBackend()


func = dependency.inject(send_welcome_email)
func()
```
