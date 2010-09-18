from tipfy import RequestHandler, Response


class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('Hello, World!')


class HandlerWithException(RequestHandler):
    def get(self, **kwargs):
        raise ValueError('ooops!')

