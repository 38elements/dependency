import typing
import dependency
from werkzeug.datastructures import ImmutableMultiDict, EnvironHeaders
from werkzeug.exceptions import HTTPException
from werkzeug.routing import Map, Rule
from werkzeug.serving import run_simple
from werkzeug.urls import url_decode
from werkzeug.wrappers import Request, Response


# Initial state
Environ = typing.NewType('Environ', dict)
URLArgs = typing.NewType('URLArgs', dict)

# Dependency injected types
Method = typing.NewType('Method', str)
Path = typing.NewType('Path', str)
Headers = EnvironHeaders
Header = typing.NewType('Header', str)
QueryParams = typing.NewType('QueryParams', ImmutableMultiDict)
QueryParam = typing.NewType('QueryParam', str)
URLArg = typing.TypeVar('URLArg')


@dependency.provider
def get_request(environ: Environ) -> Request:
    return Request(environ)


@dependency.provider
def get_method(environ: Environ) -> Method:
    return Method(environ['REQUEST_METHOD'].upper())


@dependency.provider
def get_path(environ: Environ) -> Path:
    return Path(environ['SCRIPT_NAME'] + environ['PATH_INFO'])


@dependency.provider
def get_headers(environ: Environ) -> Headers:
    return Headers(environ)


@dependency.provider
def get_header(name: dependency.ParamName, headers: Headers) -> Header:
    return Header(headers.get(name.replace('_', '-')))


@dependency.provider
def get_queryparams(environ: Environ) -> QueryParams:
    return QueryParams(url_decode(environ.get('QUERY_STRING', '')))


@dependency.provider
def get_queryparam(name: dependency.ParamName, params: QueryParams) -> QueryParam:
    return QueryParam(params.get(name))


@dependency.provider
def get_url_arg(name: dependency.ParamName, args: URLArgs) -> URLArg:
    return args.get(name)


class App():
    def __init__(self, urls):
        self.map = Map(urls)
        self.injected_funcs = {}
        dependency.set_required_state({
            'environ': Environ,
            'url_args': URLArgs
        })
        for rule in urls:
            self.injected_funcs[rule.endpoint] = dependency.inject(rule.endpoint)

    def __call__(self, environ, start_response):
        urls = self.map.bind_to_environ(environ)
        try:
            endpoint, args = urls.match()
            func = self.injected_funcs[endpoint]
            response = func(environ=environ, url_args=args)
        except HTTPException as exc:
            response = exc.get_response(environ)
        return response(environ, start_response)


def homepage(method: Method, path: Path, headers: Headers, args: URLArgs):
    import json
    content = json.dumps({
        'method': method,
        'path': path,
        'headers': dict(headers),
        'args': args
    }, indent=4).encode('utf-8')
    return Response(content)


def user(user: URLArg):
    import json
    content = json.dumps({
        'user': user
    }, indent=4).encode('utf-8')
    return Response(content)


app = App([
    Rule('/', endpoint=homepage),
    Rule('/<user>/', endpoint=user),
])


if __name__ == '__main__':
    run_simple('localhost', 8080, app)
