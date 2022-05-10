import re
import functools

from lxml.etree import fromstring, tostring
from pyigt import IGT
from pycldf.sources import Source


def parse(p):
    return fromstring(p.read_bytes().replace(b'&nbsp;', b'&#160;'))


def translate(in_, out_, s):
    tr = dict(zip(in_, out_))
    try:
        return ''.join(tr[c] for c in s)
    except (KeyError, TypeError):
        return ''


sup = functools.partial(
    translate,
    "ABCDEFGHIJKLMNOPRSTUVWXYZabcdefghijklmnoprstuvwxyz0123456789+-=()",
    "ᴬᴮᶜᴰᴱᶠᴳᴴᴵᴶᴷᴸᴹᴺᴼᴾᴿˢᵀᵁⱽᵂˣʸᶻᵃᵇᶜᵈᵉᶠᵍʰᶦʲᵏˡᵐⁿᵒᵖʳˢᵗᵘᵛʷˣʸᶻ⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾")
sub = functools.partial(translate, "aeox0123456789+-=()", "ₐₑₒₓ₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎")


def iter_text(p):
    for e in p.xpath('child::node()'):
        if getattr(e, 'tag', None):
            if e.tag == 'sc':
                yield ''.join(iter_text(e)).upper()
            elif e.tag == 'sup':
                yield sup(e.text)
            elif e.tag == 'sub':
                yield sub(e.text)
            elif e.tag == 'upper':
                if e.text:
                    yield e.text.upper()
                else:
                    raise ValueError(tostring(e))
            elif e.tag in ['xref', 'ext-link', 'table-wrap', 'disp-formula']:
                pass
            elif e.tag == 'list':
                # FIXME: '<list xmlns:mml="http://www.w3.org/1998/Math/MathML"
                #  xmlns:xlink="http://www.w3.org/1999/xlink" xmlns:xsi="http://www.w3.org/
                #  2001/XMLSchema-instance" list-type="alpha-lower">\n<list-item>
                #  <p>&#8220;Shark caught fish, but penguin did not catch fish.&#8221;
                #  </p></list-item>\n<list-item><p>&#8220;Shark caught fish, but shark
                #  did not catch penguin.&#8221;</p></list-item>\n<list-item><p>Both
                #  (a) and (b)</p></list-item>\n<list-item><p>I am not sure</p>
                #  </list-item>\n</list>'
                pass
            elif e.text:
                assert not isinstance(e.tag, str) or (e.tag in [
                    'bold', 'italic', 'underline', 'strike', 'monospace', 'inline-formula'
                ]), tostring(e)
                yield e.text
        else:
            yield str(e)


def t(s, multi=False):
    p = s.xpath('p')
    if not multi:
        assert len(p) == 1 or p[1].xpath('table-wrap') or (
                len(p) == 2 and
                ''.join(iter_text(p[1])).strip() in ['', '↔', 'ɛ elsewhere', 'ə elsewhere']), \
            '\n'.join(tostring(pp).decode('utf8') for pp in p)
        return ''.join(iter_text(p[0]))
    return '\n'.join(''.join(iter_text(pp)) for pp in p)


def parse_igt(d):
    """
    <list list-type="final-sentence">
        <list-item>
            <p>
                <italic>Tongan</italic>
                (
                    <xref ref-type="bibr" rid="B23">Otsuka 2005: 73</xref>
                )
            </p>
        </list-item>
    </list>

#
# FIXME: orthogonal layout:
#
<list list-type="sentence-gloss">
<list-item>
<list list-type="final-sentence">
<list-item><p>Velar palatalization: velars palatalize to postalveolars</p></list-item>
</list>
</list-item>
<list-item>
<list list-type="word">
<list-item><p>ba&#638;<bold>k</bold>-a</p></list-item>
<list-item><p>k&#638;o<bold>&#609;</bold>-a</p></list-item>
<list-item><p>p&#638;a<bold>x</bold></p></list-item>
</list>
<list list-type="word">
<list-item><p>&#8216;boat&#8217;</p></list-item>
<list-item><p>&#8216;circle-<sc>GEN</sc>&#8217;</p></list-item>
<list-item><p>&#8216;dust&#8217;</p></list-item>
</list>
<list list-type="word">
<list-item><p>ba&#638;<bold>&#679;</bold>-itsa</p></list-item>
<list-item><p>k&#638;o<bold>&#658;</bold>-&#601;ts</p></list-item>
<list-item><p>p&#638;a<bold>&#643;</bold>-&#601;k</p></list-item>
</list>
<list list-type="word">
<list-item><p>&#8216;boat-<sc>DIMINUTIVE</sc>&#8217;</p></list-item>
<list-item><p>&#8216;circle-<sc>DIMINUTIVE</sc>&#8217;</p></list-item>
<list-item><p>&#8216;powder&#8217;</p></list-item>
</list>
</list-item>

#
# FIXME: comments
#
<list list-type="word">
<list-item><p>Ayda&#160;&#160;&#160;&#160;(Pseudo-stripping)</p></list-item>
<list-item><p>Ayda</p></list-item>
</list>
    """
    aw, gl, tr = [], [], []
    for i, li in enumerate(d.xpath('list-item')):
        words = li.xpath("list[@list-type='word']")
        if words:
            for w in words:
                tiers = w.xpath('list-item')
                if len(tiers) != 2:
                    # We don't know how to handle alignments with more than two lines!
                    #
                    # FIXME: Detect orthogonal layout, where first (nth) word holds list words,
                    # second (n+1th) word holds list of glosses, enclosed in &#8216; and &#8217;
                    # See 4835
                    #
                    return
                aw.append(t(tiers[0]))
                gl.append(t(tiers[1]))
        fs = li.xpath("list[@list-type='final-sentence']")
        if fs:
            for i, l in enumerate(fs):
                items = l.xpath('list-item')
                for j, lii in enumerate(items):
                    tr.append(t(lii, multi=True))
                break

    return aw, gl, '\n'.join(tr)


def iter_igt(d, abbrs):
    seen, count, number, letter = set(), 0, None, None
    lang, refs = None, []
    for l in d.xpath(".//list[@list-type='gloss']"):
        numbers = [t(li.xpath('list-item')[0]) for li in l.xpath(".//list[@list-type='wordfirst']")]
        for n in numbers:
            m = re.match(r'\(([0-9]+|[iv]+)\)', n)
            if m:
                nn = m.groups()[0]
                if number:
                    letter = None
                    lang, refs = None, []
                number = nn
            m = re.fullmatch(r'([a-z])\.', n)
            if m:
                letter = m.groups()[0]
                break

        for ll in l.xpath("list-item/list[@list-type='sentence-gloss']"):
            if ll.xpath(".//list[@list-type='gloss']"):
                # there are nested examples! skip the wrapper.
                continue
            # look for language and refs:
            fs = ll.xpath("list-item/list[@list-type='final-sentence']")
            if fs:
                items = fs[0].xpath('list-item')
                if items and \
                        len(items) == 1 and \
                        (
                                items[0].xpath('p/italic') or
                                (items[0].xpath('p') and re.match(
                                    r'([A-Z][a-z]+)(\s+[A-Z][a-z]+)*\s+\(',
                                    items[0].xpath('p')[0].text or ''))):
                    # parse language name!
                    if items[0].xpath('p/italic'):
                        lname = items[0].xpath('p/italic')[0].text
                    else:
                        lname = items[0].xpath('p')[0].text.split('(')[0].strip()
                    if lname and len(lname) > 1 and lname[0].isupper():
                        lang = lname
                    for xref in items[0].xpath('p/xref'):
                        refs.append((xref.get('rid'), xref.get('ref-type'), xref.text))

            if ll.xpath("list-item/list[@list-type='word']") and not ll.xpath(".//inline-graphic"):
                res = parse_igt(ll)
                if res:
                    res = IGT(phrase=res[0], gloss=res[1], translation=res[2], abbrs=abbrs)
                    if res.primary_text not in seen:
                        count += 1
                        yield count, number, letter, lang, refs, res
                        seen.add(res.primary_text)


def names(xp):
    res = []
    for n in xp:
        try:
            if not n.xpath('surname'):
                continue
            name = n.xpath('surname')[0].text
            gn = n.xpath('given-names')
            if gn:
                name += ', {}'.format(gn[0].text)
            res.append(name)
        except:
            raise ValueError(tostring(n))
    return ' and '.join(res)


def abbreviations(doc):
    sec = doc.xpath(".//sec[title/text()='Abbreviations']")
    res = {}
    if sec:
        ps = sec[0].xpath('p')
        if not ps:
            return res
        abbr, desc = None, []
        for p in ps:
            for e in p.xpath('child::node()'):
                if getattr(e, 'tag', None):
                    if e.tag == 'sc':
                        if abbr:
                            res[abbr] = ''.join(desc)
                        abbr, desc = e.text.upper(), []
                    elif e.text:
                        desc.append(e.text)
                else:
                    desc.append(str(e))
        if abbr:
            res[abbr] = ''.join(desc)

    def clean_desc(s):
        s = s.strip()
        if s.startswith('='):
            s = s[1:].strip()
        if s.endswith(','):
            s = s[:-1].strip()
        return s
    return {k: clean_desc(v) for k, v in res.items()}


def metadata(p, doc):
    """
    """
    license = doc.xpath('.//license')[0].get('{http://www.w3.org/1999/xlink}href')
    assert 'creativecommons.org/licenses/by/' in license, license
    doi = doc.xpath(".//article-id[@pub-id-type='doi']")[0].text
    assert doi
    title = re.sub(r'\s+', ' ', ''.join(iter_text(doc.xpath(".//article-title")[0])))
    assert title

    return dict(
        ID=p.stem,
        DOI=doi,
        metalanguage='eng',
        objectlanguage=False,
        license=license,
        creators=names(doc.xpath(".//contrib[@contrib-type='author']/name")),
        title=title,
        year=doc.xpath(".//pub-date/year")[0].text,
        doc=doc,
    )


def refs(doc):
    for ref in doc.xpath('.//ref-list/ref'):
        sid = ref.get('id')
        try:
            ref = ref.xpath('element-citation')[0]
        except IndexError:
            ref = ref.xpath('mixed-citation')[0]

        genre = {
            'journal': 'article',
            'confproc': 'inproceedings'
        }.get(ref.get('publication-type'), ref.get('publication-type'))
        if genre == 'journal':
            genre = 'article'
        md = {}
        for pg in ref.xpath('person-group'):
            md[pg.get('person-group-type')] = names(pg.xpath('name'))
        if ref.xpath('string-name'):
            md['author'] = names(ref.xpath('string-name'))
        for year in ref.xpath('year'):
            md['year'] = year.text
            break
        if ref.xpath('fpage'):
            md['pages'] = ref.xpath('fpage')[0].text
            lpage = ref.xpath('lpage')
            if lpage:
                md['pages'] += '-{}'.format(lpage[0].text)
        p = ref.xpath("pub-id[@pub-id-type='doi']")
        if p:
            md['doi'] = p[0].text
        p = ref.xpath("article-title")
        if p:
            md['title'] = p[0].text
        p = ref.xpath("chapter-title")
        if p:
            genre = 'incollection'
            md['title'] = p[0].text
        p = ref.xpath('source')
        if p:
            f = {
                'incollection': 'booktitle',
                'article': 'journal',
            }.get(genre, 'title')
            md[f] = p[0].text
            if md[f].endswith('. doctoral dissertation'):
                md[f] = md[f].replace('. doctoral dissertation', '')
                genre = 'phdthesis'

        for xp, field in [
            ('conf-loc', 'address'),
            ('conf-name', 'howpublished'),
            ('conf-sponsor', 'publisher'),
            ('publisher-loc', 'address'),
            ('publisher-name', 'publisher'),
            ('volume', 'volume'),
        ]:
            p = ref.xpath(xp)
            if p:
                md[field] = p[0].text

        if genre == 'phdthesis' and 'publisher' in md:
            md['school'] = md.pop('publisher')

        yield Source(genre, sid, **md)
