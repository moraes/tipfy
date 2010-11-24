.. _guide.exception_handling:

Exception Handling
==================

Quick start
-----------
To handle application-wide uncaught exceptions, define RequestHandler classes
to handle specific HTTP error codes. For example, a handler for
**404 Not Found**:

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler, Response

   class NotFoundHandler(RequestHandler):
       def handle_exception(self, exception=None):
           # Log the exception.
           logging.exception(exception)

           # Return an error page. It could also render a template.
           return Response('Oops! I could swear this page was here!',
               status=404)


Then set the handler for 404 in the application **error_handlers** dict:

**main.py**

.. code-block:: python

   from tipfy import Tipfy
   from urls import rules

   # Instantiate the application.
   app = Tipfy(rules=rules)
   app.error_handlers[404] = 'handlers.NotFoundHandler'

   def main():
       # Run the app.
       app.run()

   if __name__ == '__main__':
       main()

You can use a single class for many HTTP error codes as well, and treat them
differently depending on the exception:

**handlers.py**

.. code-block:: python

   from tipfy import HTTPException, RequestHandler, Response

   class ErrorHandler(RequestHandler):
       messages = {
           403: 'Oops! Access to this page is not allowed!',
           404: 'Oops! I could swear this page was here!',
           500: 'Oops! Something bad occurred!',
       }

       def handle_exception(self, exception=None):
           # Log the exception.
           logging.exception(exception)

           # Default status code.
           code = 500

           # Get the specific status code if it is an HTTPException.
           if isinstance(exception, HTTPException):
               code = exception.code

           # Get the message corresponding to the status code.
           if code in self.messages:
               message = messages[code]
           else:
               message = messages[500]

           # Return an error page. It could also render a template.
           return Response(message, status=code)

Then just set the error handler in the app for all desired HTTP error codes:

**main.py**

.. code-block:: python

   # ...

   # Instantiate the application.
   app = Tipfy(rules=rules)
   for code in (403, 404, 500):
       app.error_handlers[code] = 'handlers.ErrorHandler'

   # ...

Handling exceptions in RequestHandler
-------------------------------------

Handling exceptions using middleware
------------------------------------
