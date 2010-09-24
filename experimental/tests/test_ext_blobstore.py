# -*- coding: utf-8 -*-
"""
    Tests for tipfyext.appengine.blobstore
"""
import datetime
import decimal
import time
import unittest

from tipfyext.appengine.blobstore import (CreationFormatError, parse_blob_info,
    parse_creation)


class TestParseCreation(unittest.TestCase):
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

        assert res.timetuple() == curr_date.timetuple()



class TestParseBlobInfo(unittest.TestCase):
    def test_none(self):
        assert parse_blob_info(None, 'my_field_name') is None
