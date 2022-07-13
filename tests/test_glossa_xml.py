import pytest

from linglit.glossa.xml import text, parse_citation, parse_language_name, parse_ref, iter_igt


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
        ('<list-item><p>&#8216;He will take <italic>the</italic> guests/them to the restaurant.&#8217;</p></list-item>',
         None)
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


@pytest.mark.parametrize(
    'xml,check',
    [
        ("""
        <list list-type="gloss">
            <list-item>
                <list list-type="wordfirst">
                    <list-item><p>&#160;</p></list-item>
                </list>
                <list list-type="wordfirst">
                    <list-item><p>b.</p></list-item>
                </list>
            </list-item>
            <list-item>
                <list list-type="sentence-gloss">
                    <list-item>
                        <list list-type="final-sentence">
                            <list-item><p><italic>German</italic>&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;&#160;(<xref ref-type="bibr" rid="B11">De Cesare 2014: 19</xref>, cited from <xref ref-type="bibr" rid="B17">Erdmann 1990</xref>)</p></list-item>
                        </list>
                    </list-item>
                    <list-item>
                        <list list-type="word">
                            <list-item><p>Alles</p></list-item>
                            <list-item><p>all</p></list-item>
                        </list>
                        <list list-type="word">
                            <list-item><p>was</p></list-item>
                            <list-item><p>what</p></list-item>
                        </list>
                        <list list-type="word">
                            <list-item><p>du</p></list-item>
                            <list-item><p>you</p></list-item>
                        </list>
                        <list list-type="word">
                            <list-item><p>brauchst,</p></list-item>
                            <list-item><p>need</p></list-item>
                        </list>
                        <list list-type="word">
                            <list-item><p>ist</p></list-item>
                            <list-item><p>is</p></list-item>
                        </list>
                        <list list-type="word">
                            <list-item><p>Liebe.</p></list-item>
                            <list-item><p>love</p></list-item>
                        </list>
                    </list-item>
                    <list-item>
                        <list list-type="final-sentence">
                            <list-item><p>&#8216;All you need is love.&#8217;</p></list-item>
                        </list>
                    </list-item>
                </list>
            </list-item>
        </list>
        """,
         lambda count, number, letter, lang, refs, igt, _: lang == 'German' and igt.translation == 'All you need is love.'),
        ("""<list list-type="gloss">
<list-item>
<list list-type="wordfirst">
<list-item><p>(49)</p></list-item>
</list>
</list-item>
<list-item>
<list list-type="sentence-gloss">
<list-item>
<list list-type="final-sentence">
<list-item><p><italic>Amele</italic> (<xref ref-type="bibr" rid="B100">Stirling 1993: 213</xref>)</p></list-item>
</list>
</list-item>
<list-item>
<list list-type="word">
<list-item><p>[ Ege</p></list-item>
<list-item><p>&#160;&#160;&#160;1<sc>PL</sc></p></list-item>
</list>
<list list-type="word">
<list-item><p>h-u-me-b</p></list-item>
<list-item><p>come-<sc>PRED-SS</sc>-1<sc>PL</sc></p></list-item>
</list>
<list list-type="word">
<list-item><p>] sab</p></list-item>
<list-item><p>&#160;&#160;&#160;food</p></list-item>
</list>
<list list-type="word">
<list-item><p>jo-si-a.</p></list-item>
<list-item><p>eat-3<sc>DU.TODPST</sc></p></list-item>
</list>
</list-item>
<list-item>
<list list-type="final-sentence">
<list-item><p>&#8216;We<sub><italic>i,j,k</italic></sub> came and they two<sub><italic>k,l</italic></sub> ate the food.&#8217;</p></list-item>
</list>
</list-item>
</list>
</list-item>
</list>
""",
         lambda count, number, letter, lang, refs, igt, _: igt.gloss == ['1PL', 'come-PRED-SS-1PL', 'food', 'eat-3DU.TODPST'])
    ],
)
def test_iter_igt(xml, check):
    xml = _xml(xml)
    res = list(iter_igt(xml, {}))
    assert len(res) == 1
    assert check(*res[0])
