Welcome to Tipfy!
=================

Tipfy is a small but powerful framework designed specifically for Google
App Engine. It is a lot like webapp::

  from tipfy import RequestHandler, Response

  class HelloWorldHandler(RequestHandler):
      def get(self):
          return Response('Hello, World!')


...but offers a lot of features (own authentication, sessions, i18n etc) and
other goodies that webapp misses. Everything in a modular, lightweight way,
tuned for App Engine. You use only what you need, when you need.

Read the documentation to learn more about it:

  http://www.tipfy.org/docs

For questions and comments, join our discussion group:

  http://groups.google.com/group/tipfy

And if you have any issues, open a ticket at Google Code:

  http://code.google.com/p/tipfy/


Quick howto
===========

1. Add the contents of the /source directory to your App Engine project dir.

2. Start the development server pointing to your project dir:

     $ dev_appserver.py /path/to/my/app

3. Follow the "Hello, World!" mini-tutorial from the project's documentation:

     http://www.tipfy.org/docs/tutorials/hello-world.html
