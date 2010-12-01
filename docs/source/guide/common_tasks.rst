.. _guide.common_tasks:

Common Tasks
============

Serving images from datastore
-----------------------------

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler, Response

   class ImageHandler(RequestHandler):
       def get(self, **kwargs):

           # Fetch an image from datastore.
           # image_data = ...
           # Set a response.
           response = Response(image_data)
           # Set the proper image type.
           response.headers['Content-Type'] = 'image/png'
           # Done!
           return response


Serving images from datastore using ETag
----------------------------------------
TODO


Sending a file for download
---------------------------

**handlers.py**

.. code-block:: python

   from tipfy import RequestHandler, Response

   class DownloadHandler(RequestHandler):
       def get(self, **kwargs):

           # Fetch some data from datastore.
           # data = ...

           # Name the file that will be sent to the user.
           filename = 'myfile.pdf'

           # Set a response.
           response = Response(data)
           # Set the proper content type.
           response.headers['Content-Type'] = 'application/pdf'
           # Set the file name offered for download.
           response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename

           # Done!
           return response


Service authentication using HTTP Basic Auth
--------------------------------------------
TODO


Service authentication using Google ClientLogin API
---------------------------------------------------
TODO
