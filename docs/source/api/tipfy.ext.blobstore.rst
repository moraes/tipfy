.. _api.tipfy.ext.blobstore:

tipfy.ext.blobstore
===================
This module provides request handler mixins to handle upload and serving files
from App Engine's blobstore.

Here's a simple example to upload and serve files, based on the example from
App Engine docs:

**handlers.py**

.. code-block:: python

   from google.appengine.ext import blobstore

   from tipfy import redirect_to, RequestHandler, Response, url_for
   from tipfy.ext.blobstore import BlobstoreDownloadMixin, BlobstoreUploadMixin


   class MainHandler(RequestHandler):
       def get(self):
           upload_url = blobstore.create_upload_url(url_for('blobstore/upload'))
           html = ''
           html += '<html><body>'
           html += '<form action="%s" method="POST" enctype="multipart/form-data">' % upload_url
           html += """Upload File: <input type="file" name="file"><br> <input type="submit"
               name="submit" value="Submit"> </form></body></html>"""

           return Response(html, mimetype='text/html')


   class UploadHandler(RequestHandler, BlobstoreUploadMixin):
       def post(self):
           # 'file' is the name of the file upload field in the form.
           upload_files = self.get_uploads('file')
           blob_info = upload_files[0]
           response = redirect_to('blobstore/serve', resource=blob_info.key())
           # Clear the response body.
           response.data = ''
           return response


   class ServeHandler(RequestHandler, BlobstoreDownloadMixin):
       def get(self, **kwargs):
           blob_info = blobstore.BlobInfo.get(kwargs.get('resource'))
           return self.send_blob(blob_info)


Here, ``MainHandler`` just displays an upload form. ``UploadHandler`` processes
the upload file and redirects to ``ServeHandler``, which serves the file. Here
are the URL rules for the handlers above:

**urls.py**

.. code-block:: python

   from tipfy import Rule

   def get_rules():
       rules = [
           Rule('/', endpoint='home', handler='handlers.MainHandler'),
           Rule('/upload', endpoint='blobstore/upload', handler='handlers.UploadHandler'),
           Rule('/serve/<resource>', endpoint='blobstore/serve', handler='handlers.ServeHandler'),
       ]

       return rules


.. module:: tipfy.ext.blobstore

Mixin classes
-------------
.. autoclass:: BlobstoreDownloadMixin
   :members: send_blob
.. autoclass:: BlobstoreUploadMixin
   :members: get_uploads
