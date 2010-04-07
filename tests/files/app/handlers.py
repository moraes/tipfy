import tipfy


class HomeHandler(tipfy.RequestHandler):
    def get(self, **kwargs):
        return tipfy.Response('Hello, World!')


class HandlerWithException(tipfy.RequestHandler):
    def get(self, **kwargs):
        raise ValueError('ooops!')
