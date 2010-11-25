.. _guide.common_tasks:

Common Tasks
============


Sending files for downloads
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
           response.headers['Content-Type']= 'application/pdf'
           # Set the file name offered for download.
           response.headers['Content-Disposition'] = 'attachment; filename=%s' % filename

           # Done!
           return response
