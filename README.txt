Tipfy is a small but powerful framework designed specifically for Google
App Engine. It is a lot like webapp::

  from tipfy import RequestHandler, Response

  class HelloWorldHandler(RequestHandler):
      def get(self):
          return Response('Hello, World!')


...but offers a lot of features (own authentication, sessions,
internationalization etc) and other goodies that webapp misses. Everything in a
modular, lightweight way, tuned for App Engine. You use only what you need,
when you need.

Visit www.tipfy.org/docs to learn more about it. If you have questions or
issues, post them on Tipfy's Google Group:

  http://groups.google.com/group/tipfy

Quick howto
===========

1. Add the contents of the /source directory to your App Engine project dir.

2. Start the development server pointing to your project dir:

     $ dev_appserver.py /path/to/my/app

3. Follow the "Hello, World!" mini-tutorial from the project's documentation:

     http://www.tipfy.org/docs/tutorials/hello-world.html
