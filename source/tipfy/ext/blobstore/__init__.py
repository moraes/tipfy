#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

"""Handler library for Blobstore API.

Based on original App Engine library and the adaptation made by Kay framework.

Contains handlers to help with uploading and downloading blobs.

  BlobstoreDownloadHandler: Has helper method for easily sending blobs
    to client.
  BlobstoreUploadHandler: Handler for receiving upload notification requests.
"""
import logging
import cgi
import email

from werkzeug import FileStorage

from google.appengine.ext import blobstore
from google.appengine.api import blobstore as api_blobstore

from tipfy import local


_CONTENT_DISPOSITION_FORMAT = 'attachment; filename="%s"'


class BlobstoreDownloadMixin(object):
    """Base class for creating handlers that may send blobs to users."""
    def send_blob(self, blob_key_or_info, content_type=None, save_as=None):
        """Send a blob-response based on a blob_key.

        Sets the correct response header for serving a blob.  If BlobInfo
        is provided and no content_type specified, will set request content type
        to BlobInfo's content type.

        Args:
          blob_key_or_info: BlobKey or BlobInfo record to serve.
          content_type: Content-type to override when known.
          save_as: If True, and BlobInfo record is provided, use BlobInfos
            filename to save-as.  If string is provided, use string as filename.
            If None or False, do not send as attachment.

          Raises:
            ValueError on invalid save_as parameter.
        """
        if isinstance(blob_key_or_info, blobstore.BlobInfo):
            blob_key = blob_key_or_info.key()
            blob_info = blob_key_or_info
        else:
            blob_key = blob_key_or_info
            blob_info = None

        local.response.headers[blobstore.BLOB_KEY_HEADER] = str(blob_key)

        if content_type:
            if isinstance(content_type, unicode):
                content_type = content_type.encode('utf-8')

            local.response.content_type = content_type
        else:
            del local.response.content_type

        def send_attachment(filename):
            if isinstance(filename, unicode):
                filename = filename.encode('utf-8')

            local.response.headers['Content-Disposition'] = (
                _CONTENT_DISPOSITION_FORMAT % filename)

        if save_as:
            if isinstance(save_as, basestring):
                send_attachment(save_as)
            elif blob_info and save_as is True:
                send_attachment(blob_info.filename)
            else:
                if not blob_info:
                    raise ValueError('Expected BlobInfo value for '
                        'blob_key_or_info.')
                else:
                    raise ValueError('Unexpected value for save_as')

        local.response.data = ''
        return local.response


class BlobstoreUploadMixin(object):
    """Mixin for creation blob upload handlers."""
    def get_uploads(self, field_name=None):
        """Get uploads sent to this handler.

        Args:
          field_name: Only select uploads that were sent as a specific field.

        Returns:
          A list of BlobInfo records corresponding to each upload.
          Empty list if there are no blob-info records for field_name.
        """
        if getattr(self, '__uploads', None) is None:
            self.__uploads = {}
            for key, value in local.request.files.items():
                if isinstance(value, FileStorage):
                    for option in value.headers['Content-Type'].split(';'):
                        if 'blob-key' in option:
                            self.__uploads.setdefault(key, []).append(
                                parse_blob_info(value))

            if field_name:
                try:
                    return list(self.__uploads[field_name])
                except KeyError:
                    return []
            else:
                results = []
                for uploads in self.__uploads.itervalues():
                    results += uploads

            return results


def parse_blob_info(file_storage):
  """Parse a BlobInfo record from file upload field_storage.

  Args:
    file_storage: werkzeug.FileStorage that represents uploaded blob.

  Returns:
    BlobInfo record as parsed from the field-storage instance.
    None if there was no field_storage.

  Raises:
    BlobInfoParseError when provided field_storage does not contain enough
    information to construct a BlobInfo object.
  """
  if file_storage is None:
    return None

  field_name = file_storage.name

  def get_value(dict, name):
    value = dict.get(name, None)
    if value is None:
      raise blobstore.BlobInfoParseError(
        'Field %s has no %s.' % (field_name, name))
    return value

  filename = file_storage.filename
  content_type, cdict = cgi.parse_header(file_storage.headers['Content-Type'])
  blob_key = blobstore.BlobKey(get_value(cdict, 'blob-key'))

  upload_content = email.message_from_file(file_storage.stream)
  content_type = get_value(upload_content, 'content-type')
  size = get_value(upload_content, 'content-length')
  creation_string = get_value(upload_content,
                              blobstore.UPLOAD_INFO_CREATION_HEADER)

  try:
    size = int(size)
  except (TypeError, ValueError):
    raise blobstore.BlobInfoParseError(
      '%s is not a valid value for %s size.' % (size, field_name))

  try:
    creation = api_blobstore.parse_creation(creation_string)
  except blobstore.CreationFormatError, e:
    raise blobstore.BlobInfoParseError(
      'Could not parse creation for %s: %s' % (
        field_name, str(e)))

  return blobstore.BlobInfo(blob_key,
                            {'content_type': content_type,
                             'creation': creation,
                             'filename': filename,
                             'size': size,
                             })
