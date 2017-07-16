import typing
import dependency
from werkzeug.datastructures import EnvironHeaders
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.wrappers import Request, Response


Environ = typing.NewType('Environ', dict)
Method = typing.NewType('Method', str)
Headers = EnvironHeaders
Path = typing.NewType('Path', str)
URLArgs = typing.NewType('URLArgs', dict)


@dependency.provider
def get_request(environ: Environ) -> Request:
    return Request(environ)


@dependency.provider
def get_method(environ: Environ) -> Method:
    return environ['REQUEST_METHOD'].upper()


@dependency.provider
def get_path(environ: Environ) -> Path:
    return environ['SCRIPT_NAME'] + environ['PATH_INFO']


@dependency.provider
def get_headers(environ: Environ) -> Headers:
    return Headers(environ)


# body
# urlargs
# urlarg
# header
# queryparams
# queryparam


class App():
    def __init__(self, urls):
        self.url_map = Map(urls)
        self.injected_funcs = {}
        dependency.required_state({'environ': Environ, 'url_args': URLArgs})
        for rule in urls:
            self.injected_funcs[rule.endpoint] = dependency.inject(rule.endpoint)

    def __call__(self, environ, start_response):
        urls = self.url_map.bind_to_environ(environ)
        try:
            endpoint, args = urls.match()
            func = self.injected_funcs[endpoint]
            response = func(environ=environ, url_args=args)
        except HTTPException as exc:
            response = exc.get_response(environ)
        return response(environ, start_response)


def homepage(method: Method, path: Path, headers: Headers, args: URLArgs):
    import json
    print(headers)
    content = json.dumps({
        'method': method,
        'path': path,
        'headers': dict(headers),
        'args': args
    }, indent=4)
    return Response(content)


app = App([
    Rule('/', endpoint=homepage),
    Rule('/<first>/', endpoint=homepage),
    Rule('/<first>/<int:second>/', endpoint=homepage),
])


if __name__ == '__main__':
    run_simple('localhost', 8080, app)
