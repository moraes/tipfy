import os
import unittest

from tipfy import template

import test_utils

TEMPLATES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
    'resources', 'templates'))
TEMPLATES_ZIP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__),
    'resources', 'templates.zip'))


class TestTemplate(test_utils.BaseTestCase):
    def test_generate(self):
        t = template.Template('<html>{{ myvalue }}</html>')
        self.assertEqual(t.generate(myvalue='XXX'), '<html>XXX</html>')

    def test_loader(self):
        loader = template.Loader(TEMPLATES_DIR)
        t = loader.load('template_tornado1.html')
        self.assertEqual(t.generate(students=['calvin', 'hobbes', 'moe']), '\n\ncalvin\n\n\n\nhobbes\n\n\n\nmoe\n\n\n')

    def test_loader2(self):
        loader = template.ZipLoader(TEMPLATES_ZIP_DIR, 'templates')
        t = loader.load('template1.html')
        self.assertEqual(t.generate(message='Hello, World!'), 'Hello, World!\n')


if __name__ == '__main__':
    test_utils.main()
