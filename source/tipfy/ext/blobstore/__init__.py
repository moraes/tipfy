# -*- coding: utf-8 -*-
"""
    tipfy.ext.blobstore
    ~~~~~~~~~~~~~~~~~~~

    Handler library for Blobstore API.

    Contains handler mixins to help with uploading and downloading blobs.

    BlobstoreDownloadMixin: Has helper method for easily sending blobs
    to client.

    BlobstoreUploadMixin: mixin for receiving upload notification requests.

    Based on the original App Engine library and the adaptation to Werkzeug
    from Kay framework.

    :copyright: 2007 Google Inc.
    :copyright: 2009 Accense Technology, Inc. All rights reserved.
    :copyright: 2010 tipfy.org.
    :license: Apache 2.0 License, see LICENSE.txt for more details.
"""
import logging
import cgi
import email

from google.appengine.ext import blobstore
from google.appengine.api import blobstore as api_blobstore

from werkzeug import FileStorage, Response

from tipfy import local


_CONTENT_DISPOSITION_FORMAT = 'attachment; filename="%s"'


class BlobstoreDownloadMixin(object):
    """Mixin for handlers that may send blobs to users."""
    def send_blob(self, blob_key_or_info, content_type=None, save_as=None):
        """Sends a blob-response based on a blob_key.

        Sets the correct response header for serving a blob.  If BlobInfo
        is provided and no content_type specified, will set request content type
        to BlobInfo's content type.

        :param blob_key_or_info:
            BlobKey or BlobInfo record to serve.
        :param content_type:
            Content-type to override when known.
        :param save_as:
            If ``True``, and BlobInfo record is provided, use BlobInfos filename
            to save-as. If string is provided, use string as filename. If
            ``None`` or ``False``, do not send as attachment.
        :return:
            A ``werkzeug.Response`` object.
        :raise:
            ``ValueError`` on invalid save_as parameter.
        """
        if isinstance(blob_key_or_info, blobstore.BlobInfo):
            blob_key = blob_key_or_info.key()
            blob_info = blob_key_or_info
        else:
            blob_key = blob_key_or_info
            blob_info = None

        headers = {blobstore.BLOB_KEY_HEADER: str(blob_key)}

        if content_type:
            if isinstance(content_type, unicode):
                content_type = content_type.encode('utf-8')

            headers['Content-Type'] = content_type
        else:
            headers['Content-Type'] = ''

        def send_attachment(filename):
            if isinstance(filename, unicode):
                filename = filename.encode('utf-8')

            headers['Content-Disposition'] = (
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

        return Response('', headers=headers, status=302)


class BlobstoreUploadMixin(object):
    """Mixin for blob upload handlers."""
    def get_uploads(self, field_name=None):
        """Returns uploads sent to this handler.

        :param field_name:
            Only select uploads that were sent as a specific field.
        :return:
            A list of BlobInfo records corresponding to each upload. Empty list
            if there are no blob-info records for field_name.
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

    :param file_storage:
        ``werkzeug.FileStorage`` that represents uploaded blob.
    :return:
        BlobInfo record as parsed from the field-storage instance.
        ``None`` if there was no field_storage.
    :raise:
        BlobInfoParseError when provided field_storage does not contain enough
        information to construct a BlobInfo object.
    """
    if file_storage is None:
        return None

    field_name = file_storage.name

    def get_value(dict, name):
        value = dict.get(name, None)
        if value is None:
            raise blobstore.BlobInfoParseError('Field %s has no %s.' %
                (field_name, name))

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
            'Could not parse creation for %s: %s' % (field_name, str(e)))

    return blobstore.BlobInfo(blob_key, {
        'content_type': content_type,
        'creation': creation,
        'filename': filename,
        'size': size,
    })
