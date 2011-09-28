import inspect
import os
import unittest
from pybbcode.parser import Parser

class TestBBCodeParser(unittest.TestCase):
    def _to_html(self, bbcode):
        return Parser().to_html(bbcode, True)

    def _read_file(self, name):
        with open(os.path.join(os.path.dirname(inspect.getfile(self.__class__)), 'static', name)) as f:
            return f.read()

    def _assertEqual(self, name):
        self.assertEqual(self._to_html(self._read_file(name + '.bbcode')), self._read_file(name + '.html'))

    def test_simple_tag(self):
        tests= [
            ('[b]Hello[/b]', "<strong>Hello</strong>"),
            ('[i]Italic[/i]', "<em>Italic</em>"),
            ('[s]Strike[/s]', "<strike>Strike</strike>"),
            ('[u]underlined[/u]', "<u>underlined</u>"),
        ]

        for test, result in tests:
            self.assertEqual(self._to_html(test), result)

    def test_links(self):
        tests= [
            ('[link=http://guildwork.com]link1[/link]', '<a href="http://guildwork.com" target="_blank">link1</a>'),
            ('[link="http://guildwork.com"]link2[/link]', '<a href="http://guildwork.com" target="_blank">link2</a>'),
            ('[link]http://guildwork.com[/link]', '<a href="http://guildwork.com" target="_blank">http://guildwork.com</a>')
        ]
 
        for test, result in tests:
            self.assertEqual(self._to_html(test), result)

    def test_document1(self):
        self._assertEqual('document1')

    def test_document2(self):
        self._assertEqual('document2')

if __name__ == '__main__':
    unittest.main()