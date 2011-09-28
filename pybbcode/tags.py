import re

_PARAM_RE = re.compile(r"""^["'](.+)["']$""")

_NEWLINE_RE = re.compile('\\r?\n')
_LINE_BREAK = u'<br />'

_ESCAPE_RE = re.compile('[&<>"]')
_ESCAPE_DICT = {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}

_URL_RE = re.compile(
    ur'''\b((?:([\w-]+):(/{1,3})|www[.])'(?:(?:(?:[^\s&()]|&amp;|&quot;)*'''
    ur'''(?:[^!"#$%&'()*+,.:;<=>?@\[\]^`{|}~\s]))|(?:\((?:[^\s&()]|&amp;|&quot;)*\)))+)'''
)

_COSMETIC_DICT = {
    u'--': u'&ndash;',
    u'---': u'&mdash;',
    u'...': u'&#8230;',
    u'(c)': u'&copy;',
    u'(reg)': u'&reg;',
    u'(tm)': u'&trade;',
}
_COSMETIC_RE = re.compile(u'|'.join(re.escape(key) for key in _COSMETIC_DICT.keys()))

def _cosmetic_replace(s):
    def repl(match):
        item = match.group(0)
        return _COSMETIC_DICT.get(item, item)

    return _COSMETIC_RE.sub(repl, s)

class Tag(object):
    CLOSED_BY = []
    SELF_CLOSE = False
    STRIP_INNER = False

    def __init__(self, parser, name=None, parent=None, text=u'', params=None):
        self.parser = parser
        
        self.name = name
        self.text = text

        self.parent = parent

        if parent:
            parent.children.append(self)

        self._raw_params = params or []
        self._params = None

        self.children = []

    @property
    def params(self):
        if self._params is None:
            self._params = {}

            if self._raw_params:
                for argument in self._raw_params:
                    if len(argument) == 2:
                        value = argument[1]

                        if value:
                            try:
                                value = _PARAM_RE.findall(value)[0]
                            except IndexError:
                                pass

                        self.params[argument[0]] = value

        return self._params

    def get_content(self, raw=False):
        if raw:
            pieces = [self.text]
        else:
            pieces = [_NEWLINE_RE.sub(_LINE_BREAK, self.linkify(self.escape(self.text)))]

        if pieces[0]:
            pieces[0] = _cosmetic_replace(pieces[0])

        children = self.children

        for child in children:
            if raw:
                pieces.append(child.to_bbcode())
            else:
                pieces.append(child.to_html())
                
        content = ''.join(pieces)

        if not raw and self.STRIP_INNER:
            content = content.strip()

            while content.startswith(_LINE_BREAK):
                content = content[len(_LINE_BREAK):]

            while content.endswith(_LINE_BREAK):
                content = content[:-len(_LINE_BREAK)]

            content = content.strip()

        return content

    def to_bbcode(self, content_as_html=False):
        pieces = []

        if self.name is not None:
            if self.params:
                params = ' '.join(u'='.join(item) for item in self.params.items())

                if self.name in self.params:
                    pieces.append(u'[%s]' % params)
                else:
                    pieces.append(u'[%s %s]' % (self.name, params))
            else:
                pieces.append(u'[%s]' % self.name)

        pieces.append(self.get_content(not content_as_html))

        if self.name is not None:
            pieces.append(u'[/%s]' % self.name)

        return ''.join(pieces)

    def _to_html(self):
        return self.to_bbcode(True),

    def to_html(self):
        return ''.join(self._to_html())

    def escape(self, value):
        """Escapes a string so it is valid within XML or XHTML."""
        return _ESCAPE_RE.sub(lambda match: _ESCAPE_DICT[match.group(0)], value)

    def linkify(self, text):
        def make_link(m):
            url = m.group(1)
            proto = m.group(2)

            if proto and proto not in ['http', 'https']:
                return url # bad protocol, no linkify

            href = m.group(1)

            if not proto:
                href = 'http://' + href # no proto specified, use http

            return u'<a href="%s" target="_blank">%s</a>' % (href, url)

        return _URL_RE.sub(make_link, text)

class CodeTag(Tag):
    def _to_html(self):
        if self.params.get('code') == 'inline':
            return u'<code>', self.get_content(True), u'</code>'

        lang = self.params.get('lang')

        if lang:
            return u'<pre class="prettyprint lang-%s">' % lang, self.get_content(True), u'</pre>',
        else:
            return u'<pre>', self.get_content(True), u'</pre>',

class ImageTag(Tag):
    def _to_html(self):
        attributes = {
            'src': self.get_content(True).strip(),
        }

        if 'width' in self.params:
            attributes['width'] = self.params['width']

        if 'height' in self.params:
            attributes['height'] = self.params['height']

        return u'<img %s />' % ' '.join('%s="%s"' % item for item in attributes.items()),
    
class SizeTag(Tag):
    def _to_html(self):
        size = self.params.get('size')

        try:
            size = int(size)
        except ValueError:
            size = None

        if size is None:
            return self.get_content()

        return u'<span style="font-size:%spx">' % size, self.get_content(), u'</span>',

class ColorTag(Tag):
    def _to_html(self):
        color = self.params.get('color')

        if not color:
            return self.get_content()

        return u'<span style="color:%s">' % color, self.get_content(), u'</span>',

class CenterTag(Tag):
    def _to_html(self):
        return u'<div style="text-align:center;">', self.get_content(), u'</div>',

class RightTag(Tag):
    def _to_html(self):
        return u'<div style="float:right;">', self.get_content(), u'</div>',

class HorizontalRuleTag(Tag):
    SELF_CLOSE = True

    def _to_html(self):
        return u'<hr />',

class ListTag(Tag):
    STRIP_INNER = True

    def _to_html(self):
        list_type = self.params.get('list')

        if list_type == '1':
            return u'<ol>', self.get_content(), u'</ol>',
        elif list_type == 'a':
            return u'<ol style="list-style-type:lower-alpha;">', self.get_content(), u'</ol>',
        elif list_type == 'A':
            return u'<ol style="list-style-type:upper-alpha;">', self.get_content(), u'</ol>',
        else:
            return u'<ul>', self.get_content(), u'</ul>',

class ListItemTag(Tag):
    CLOSED_BY = ['*', '/list']
    STRIP_INNER = True

    def _to_html(self):
        return u'<li>', self.get_content(), u'</li>',

class QuoteTag(Tag):
    STRIP_INNER = True
    
    def _to_html(self):
        pieces = [u'<blockquote>', self.get_content()]

        citation = self.params.get('quote')

        if citation:
            pieces.append(u'<small>')
            pieces.append(citation)
            pieces.append(u'</small>')

        pieces.append(u'</blockquote>')

        return pieces

class LinkTag(Tag):
    SAFE_CHARS = frozenset(
        'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        'abcdefghijklmnopqrstuvwxyz'
        '0123456789'
        '_.-=/&?:%&#'
    )

    def _to_html(self):
        url = (self.params.get(self.name) or self.get_content(True)).strip()

        if u'javascript:' in url.lower():
            return u''

        if u':' not in url:
          url = u'http://' + url

        url = ''.join([c if c in LinkTag.SAFE_CHARS else '%%%02X' % ord(c) for c in url])
        
        if url:
            return u'<a href="%s" target="_blank">%s</a>' % (url, self.get_content())
        else:
            return self.get_content()

def create_simple_tag(name):
    return type('%sTag' % name.title(), (Tag,), {
        '_to_html': lambda self: (u'<%s>' % name, self.get_content(), u'</%s>' % name,)
    })

BUILTIN_TAGS = {
    'b': create_simple_tag('strong'),
    'i': create_simple_tag('em'),
    'u': create_simple_tag('u'),
    's': create_simple_tag('strike'),
    'h1': create_simple_tag('h1'),
    'h2': create_simple_tag('h2'),
    'h3': create_simple_tag('h3'),
    'h4': create_simple_tag('h4'),
    'h5': create_simple_tag('h5'),
    'h6': create_simple_tag('h6'),
    'pre': create_simple_tag('pre'),
    'code': CodeTag,
    'hr': HorizontalRuleTag,
    'img': ImageTag,
    'size': SizeTag,
    'center': CenterTag,
    'right': RightTag,
    'color': ColorTag,
    'list': ListTag,
    '*': ListItemTag,
    'quote': QuoteTag,
    'url': LinkTag,
    'link': LinkTag,
}