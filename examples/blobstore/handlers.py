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
