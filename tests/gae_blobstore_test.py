# -*- coding: utf-8 -*-
"""
	Tests for tipfy.appengine.blobstore
"""
import datetime
import decimal
import email
import StringIO
import time
import unittest

from google.appengine.ext import blobstore

from tipfy.appengine.blobstore import (CreationFormatError, parse_blob_info,
	parse_creation)

from werkzeug import FileStorage

import test_utils


class TestParseCreation(test_utils.BaseTestCase):
	"""YYYY-mm-dd HH:MM:SS.ffffff"""
	def test_invalid_format(self):
		self.assertRaises(CreationFormatError, parse_creation, '2010-05-20 6:20:35', 'my_field_name')

	def test_invalid_format2(self):
		self.assertRaises(CreationFormatError, parse_creation, '2010-05-20 6:20:35.1234.5678', 'my_field_name')

	def test_invalid_format3(self):
		self.assertRaises(CreationFormatError, parse_creation, 'youcannot.parseme', 'my_field_name')

	def test_parse(self):
		timestamp = time.time()
		parts = str(timestamp).split('.', 1)
		ms = parts[1][:4]
		timestamp = decimal.Decimal(parts[0] + '.' + ms)
		curr_date = datetime.datetime.fromtimestamp(timestamp)

		to_convert = '%s.%s' % (curr_date.strftime('%Y-%m-%d %H:%M:%S'), ms)

		res = parse_creation(to_convert, 'my_field_name')

		self.assertEqual(res.timetuple(), curr_date.timetuple())



class TestParseBlobInfo(test_utils.BaseTestCase):
	def test_none(self):
		self.assertEqual(parse_blob_info(None, 'my_field_name'), None)

	def test_file(self):
		stream = StringIO.StringIO()
		stream.write("""\
Content-Type: application/octet-stream
Content-Length: 1
X-AppEngine-Upload-Creation: 2010-10-01 05:34:00.000000
""")
		stream.seek(0)
		headers = {}
		headers['Content-Type'] = 'image/png; blob-key=foo'

		f = FileStorage(stream=stream, headers=headers)
		self.assertNotEqual(parse_blob_info(f, 'my_field_name'), None)

	def test_invalid_size(self):
		stream = StringIO.StringIO()
		stream.write("""\
Content-Type: application/octet-stream
Content-Length: zzz
X-AppEngine-Upload-Creation: 2010-10-01 05:34:00.000000
""")
		stream.seek(0)
		headers = {}
		headers['Content-Type'] = 'image/png; blob-key=foo'

		f = FileStorage(stream=stream, headers=headers)
		self.assertRaises(blobstore.BlobInfoParseError, parse_blob_info,f, 'my_field_name')

	def test_invalid_CREATION(self):
		stream = StringIO.StringIO()
		stream.write("""\
Content-Type: application/octet-stream
Content-Length: 1
X-AppEngine-Upload-Creation: XXX
""")
		stream.seek(0)
		headers = {}
		headers['Content-Type'] = 'image/png; blob-key=foo'

		f = FileStorage(stream=stream, headers=headers)
		self.assertRaises(blobstore.BlobInfoParseError, parse_blob_info,f, 'my_field_name')


if __name__ == '__main__':
	test_utils.main()
