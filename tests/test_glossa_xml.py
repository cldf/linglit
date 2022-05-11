import pytest

from linglit.glossa.xml import text, parse_citation, parse_language_name, parse_ref


def _xml(s):
    return '<root>{}</root>'.format(s)


@pytest.mark.parametrize(
    'xml,check',
    [
        (
            '<ref id="B67"><label>67</label><mixed-citation publication-type="thesis">'
            '<string-name><surname>Santilli</surname>, <given-names>Enzo</given-names>'
            '</string-name>. <year>2014</year>. <source>Italian comparatives: a case of '
            'overabundance</source>. doctoral dissertation, <publisher-name>University '
            'of Aquila</publisher-name> dissertation.</mixed-citation></ref>',
            lambda src: src.genre == 'phdthesis'),
        (
            """<ref id="B7">
<label>7</label>
<element-citation publication-type="thesis">
<person-group person-group-type="author">
<name>
<surname>Cedergren</surname>
<given-names>Henrietta</given-names>
</name>
</person-group>
<source>The interplay of social and linguistic factors in Panama;. doctoral dissertation</source>
<year iso-8601-date="1973">1973</year>
<publisher-loc>Ithaca, NY</publisher-loc>
<publisher-name>Cornell University</publisher-name>
</element-citation>
</ref>
""",
            lambda src: src.genre == 'phdthesis' and 'Cedergren, Henrietta' in src['author']),
    ]
)
def test_parse_ref(xml, check):
    assert check(parse_ref(xml))


@pytest.mark.parametrize(
    'xml,res',
    [
        ('<upper>abc</upper>d', 'ABCd'),
        ('<xref>abc</xref>d', 'abcd'),
        ('<table-wrap>abc</table-wrap>d', 'd'),
    ]
)
def test_iter_text(xml, res):
    assert text(_xml(xml)) == res


@pytest.mark.parametrize(
    'xml,res',
    [
        ('<list-item><p>&#160;&#160;<sub><sc>Modern Portuguese</sc></sub></p></list-item>',
         'Modern Portuguese'),
        ('<list-item><p>Modern Portuguese (stuff)</p></list-item>',
         'Modern Portuguese'),
    ]
)
def test_parse_language_name(xml, res):
    assert parse_language_name(xml) == res


def test_parse_citation():
    s = '<list-item><p>&#8220;&#8230; where his name was written.&#8221;&#160;&#160;&#160;&#160;' \
        '&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;' \
        '&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;' \
        '&#160;&#160;&#160;&#160;<sub>Graal,1245, cited from Labrousse (<xref ref-type="bibr" ' \
        'rid="B27">2018: 1620</xref>)</sub></p></list-item>'
    assert parse_citation(s)[0] == 'Graal,1245, cited from Labrousse (2018: 1620)'