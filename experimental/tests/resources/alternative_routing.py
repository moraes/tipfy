from tipfy import RequestHandler, Response

class HomeHandler(RequestHandler):
    def get(self, **kwargs):
        return Response('home-get')

    def foo(self, **kwargs):
        return Response('home-foo')

    def bar(self, **kwargs):
        return Response('home-bar')


class OtherHandler(RequestHandler):
    def foo(self, **kwargs):
        return Response('other-foo')

    def bar(self, **kwargs):
        return Response('other-bar')
