import pytest
from lxml.etree import fromstring

from linglit.glossa.xml import iter_text


def _xml(s):
    return fromstring('<root>{}</root>'.format(s))


@pytest.mark.parametrize(
    'xml,text',
    [
        ('<upper>abc</upper>d', 'ABCd'),
        ('<xref>abc</xref>d', 'd'),
    ]
)
def test_iter_text(xml, text):
    assert ''.join(iter_text(_xml(xml))) == text
