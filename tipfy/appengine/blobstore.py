# -*- coding: utf-8 -*-
"""
    tipfy.appengine.blobstore
    ~~~~~~~~~~~~~~~~~~~~~~~~~

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
import cgi
import cStringIO
import datetime
import email
import logging
import re
import sys
import time

from google.appengine.ext import blobstore
from google.appengine.api import blobstore as api_blobstore

from webob import byterange

from werkzeug import FileStorage, Response

_BASE_CREATION_HEADER_FORMAT = '%Y-%m-%d %H:%M:%S'
_CONTENT_DISPOSITION_FORMAT = 'attachment; filename="%s"'

_SEND_BLOB_PARAMETERS = frozenset(['use_range'])

_RANGE_NUMERIC_FORMAT = r'([0-9]*)-([0-9]*)'
_RANGE_FORMAT = r'([a-zA-Z]+)=%s' % _RANGE_NUMERIC_FORMAT
_RANGE_FORMAT_REGEX = re.compile('^%s$' % _RANGE_FORMAT)
_UNSUPPORTED_RANGE_FORMAT_REGEX = re.compile(
    '^%s(?:,%s)+$' % (_RANGE_FORMAT, _RANGE_NUMERIC_FORMAT))
_BYTES_UNIT = 'bytes'


class CreationFormatError(api_blobstore.Error):
  """Raised when attempting to parse bad creation date format."""


class Error(Exception):
  """Base class for all errors in blobstore handlers module."""


class RangeFormatError(Error):
  """Raised when Range header incorrectly formatted."""


class UnsupportedRangeFormatError(RangeFormatError):
  """Raised when Range format is correct, but not supported."""


def _check_ranges(start, end, use_range_set, use_range, range_header):
    """Set the range header.

    Args:
        start: As passed in from send_blob.
        end: As passed in from send_blob.
        use_range_set: Use range was explcilty set during call to send_blob.
        use_range: As passed in from send blob.
        range_header: Range header as received in HTTP request.

    Returns:
        Range header appropriate for placing in blobstore.BLOB_RANGE_HEADER.

    Raises:
        ValueError if parameters are incorrect.  This happens:
          - start > end.
          - start < 0 and end is also provided.
          - end < 0
          - If index provided AND using the HTTP header, they don't match.
            This is a safeguard.
    """
    if end is not None and start is None:
        raise ValueError('May not specify end value without start.')

    use_indexes = start is not None
    if use_indexes:
        if end is not None:
            if start > end:
                raise ValueError('start must be < end.')

        range_indexes = byterange.Range.serialize_bytes(_BYTES_UNIT, [(start,
            end)])

    if use_range_set and use_range and use_indexes:
        if range_header != range_indexes:
            raise ValueError('May not provide non-equivalent range indexes '
                       'and range headers: (header) %s != (indexes) %s'
                       % (range_header, range_indexes))

    if use_range and range_header is not None:
        return range_header
    elif use_indexes:
        return range_indexes
    else:
        return None


class BlobstoreDownloadMixin(object):
    """Mixin for handlers that may send blobs to users."""
    __use_range_unset = object()

    def send_blob(self, blob_key_or_info, content_type=None, save_as=None,
        start=None, end=None, **kwargs):
        """Sends a blob-response based on a blob_key.

        Sets the correct response header for serving a blob.  If BlobInfo
        is provided and no content_type specified, will set request content type
        to BlobInfo's content type.

        :param blob_key_or_info:
            BlobKey or BlobInfo record to serve.
        :param content_type:
            Content-type to override when known.
        :param save_as:
            If True, and BlobInfo record is provided, use BlobInfos filename
            to save-as. If string is provided, use string as filename. If
            None or False, do not send as attachment.
        :returns:
            A :class:`tipfy.Response` object.
        :raises:
            ``ValueError`` on invalid save_as parameter.
        """
        # Response headers.
        headers = {}

        if set(kwargs) - _SEND_BLOB_PARAMETERS:
            invalid_keywords = []
            for keyword in kwargs:
                if keyword not in _SEND_BLOB_PARAMETERS:
                    invalid_keywords.append(keyword)

            if len(invalid_keywords) == 1:
                raise TypeError('send_blob got unexpected keyword argument '
                    '%s.' % invalid_keywords[0])
            else:
                raise TypeError('send_blob got unexpected keyword arguments: '
                    '%s.' % sorted(invalid_keywords))

        use_range = kwargs.get('use_range', self.__use_range_unset)
        use_range_set = use_range is not self.__use_range_unset

        if use_range:
            self.get_range()

        range_header = _check_ranges(start,
                                     end,
                                     use_range_set,
                                     use_range,
                                     self.request.headers.get('range', None))

        if range_header is not None:
            headers[blobstore.BLOB_RANGE_HEADER] = range_header

        if isinstance(blob_key_or_info, blobstore.BlobInfo):
            blob_key = blob_key_or_info.key()
            blob_info = blob_key_or_info
        else:
            blob_key = blob_key_or_info
            blob_info = None

        headers[blobstore.BLOB_KEY_HEADER] = str(blob_key)

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

        return Response('', headers=headers)

    def get_range(self):
        """Get range from header if it exists.

        Returns:
          Tuple (start, end):
            start: Start index.  None if there is None.
            end: End index.  None if there is None.
          None if there is no request header.

        Raises:
          UnsupportedRangeFormatError: If the range format in the header is
            valid, but not supported.
          RangeFormatError: If the range format in the header is not valid.
        """
        range_header = self.request.headers.get('range', None)
        if range_header is None:
            return None

        try:
            original_stdout = sys.stdout
            sys.stdout = cStringIO.StringIO()
            try:
                parsed_range = byterange.Range.parse_bytes(range_header)
            finally:
                sys.stdout = original_stdout
        except TypeError, err:
            raise RangeFormatError('Invalid range header: %s' % err)

        if parsed_range is None:
            raise RangeFormatError('Invalid range header: %s' % range_header)

        units, ranges = parsed_range
        if len(ranges) != 1:
            raise UnsupportedRangeFormatError(
                'Unable to support multiple range values in Range header.')

        if units != _BYTES_UNIT:
            raise UnsupportedRangeFormatError(
                'Invalid unit in range header type: %s', range_header)

        return ranges[0]


class BlobstoreUploadMixin(object):
    """Mixin for blob upload handlers."""
    def get_uploads(self, field_name=None):
        """Returns uploads sent to this handler.

        :param field_name:
            Only select uploads that were sent as a specific field.
        :returns:
            A list of BlobInfo records corresponding to each upload. Empty list
            if there are no blob-info records for field_name.
        """
        if getattr(self, '_BlobstoreUploadMixin__uploads', None) is None:
            self.__uploads = {}
            for key, value in self.request.files.items():
                if isinstance(value, FileStorage):
                    for option in value.headers['Content-Type'].split(';'):
                        if 'blob-key' in option:
                            self.__uploads.setdefault(key, []).append(
                                parse_blob_info(value, key))

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


def parse_blob_info(file_storage, field_name=None):
    """Parse a BlobInfo record from file upload field_storage.

    :param file_storage:
        ``werkzeug.FileStorage`` that represents uploaded blob.
    :returns:
        BlobInfo record as parsed from the field-storage instance.
        None if there was no field_storage.
    :raises:
        BlobInfoParseError when provided field_storage does not contain enough
        information to construct a BlobInfo object.
    """
    if file_storage is None:
        return None

    field_name = field_name or file_storage.name

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
        creation = parse_creation(creation_string, field_name)
    except CreationFormatError, e:
        raise blobstore.BlobInfoParseError(
            'Could not parse creation for %s: %s' % (field_name, str(e)))

    return blobstore.BlobInfo(blob_key, {
        'content_type': content_type,
        'creation': creation,
        'filename': filename,
        'size': size,
    })


def parse_creation(creation_string, field_name):
    """Parses upload creation string from header format.

    Parse creation date of the format:

      YYYY-mm-dd HH:MM:SS.ffffff

      Y: Year
      m: Month (01-12)
      d: Day (01-31)
      H: Hour (00-24)
      M: Minute (00-59)
      S: Second (00-59)
      f: Microsecond

    Args:
      creation_string: String creation date format.

    Returns:
      datetime object parsed from creation_string.

    Raises:
      _CreationFormatError when the creation string is formatted incorrectly.
    """
    split_creation_string = creation_string.split('.', 1)
    if len(split_creation_string) != 2:
        raise CreationFormatError(
            'Could not parse creation %s in field %s.' % (creation_string,
                                                            field_name))
    timestamp_string, microsecond = split_creation_string

    try:
        timestamp = time.strptime(timestamp_string,
                                  _BASE_CREATION_HEADER_FORMAT)
        microsecond = int(microsecond)
    except ValueError:
        raise CreationFormatError('Could not parse creation %s in field %s.'
                                  % (creation_string, field_name))

    return datetime.datetime(*timestamp[:6] + tuple([microsecond]))
