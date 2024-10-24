import re
import functools

from clldutils.misc import nfilter
from lxml.etree import fromstring, tostring
from pyigt import IGT
from pycldf.sources import Source


def element(s):
    if isinstance(s, str):
        s = fromstring(s)
    return s


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


def iter_text(p, strict=True):
    for e in p.xpath('child::node()'):
        if getattr(e, 'tag', None):
            if e.tag == 'sc':
                yield text(e, strict=strict).upper()
            elif e.tag == 'italic':
                yield text(e, strict=strict)
            elif e.tag == 'sup':
                yield sup(e.text)
            elif e.tag == 'sub':
                yield sub(e.text)
            elif e.tag == 'upper':
                if e.text:
                    yield e.text.upper()
                else:  # pragma: no cover
                    raise ValueError(tostring(e))
            elif e.tag in ['xref', 'ext-link']:
                yield e.text
            elif e.tag in ['table-wrap', 'disp-formula']:
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
                pass  # pragma: no cover
            elif e.text:
                if strict:
                    assert not isinstance(e.tag, str) or (e.tag in [
                        'bold', 'italic', 'underline', 'strike', 'monospace', 'inline-formula'
                    ]), tostring(e)
                yield e.text
        else:
            yield str(e)


def parse_citation(s):
    refs = []
    s = element(s)
    sub = s.xpath('p/sub')
    if sub and sub[0].xpath('xref'):
        for xref in sub[0].xpath('xref'):
            refs.append((xref.get('rid'), xref.get('ref-type'), xref.text))
        return text(sub[0]), refs


def text(e, strict=True):
    return ''.join(nfilter(iter_text(element(e), strict=strict)))


def t(s, multi=False):
    p = s.xpath('p')
    if not multi:
        assert len(p) == 1 or p[1].xpath('table-wrap') or (
                len(p) == 2 and  # noqa: W504
                text(p[1]).strip() in ['', '↔', 'ɛ elsewhere', 'ə elsewhere']), \
            '\n'.join(tostring(pp).decode('utf8') for pp in p)
        return text(p[0])
    return '\n'.join(text(pp) for pp in p)


def parse_igt(d):
    """
    #
    # FIXME: orthogonal layout - see tests/glossa/6371.xml
    #
    """
    comment, refs = [], []
    comment_pattern = re.compile(r'\s\s+\(([^)]+)\)$')
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
                word = t(tiers[0])
                m = comment_pattern.search(word)
                if m:
                    comment.append(m.groups()[0])
                    word = word[:m.start()]
                aw.append(word.strip())
                gl.append(t(tiers[1]).strip())
        if aw:  # Look for translation only in final-sentence items **after** the aligned text.
            fs = li.xpath("list[@list-type='final-sentence']")
            if fs:
                for i, l in enumerate(fs):
                    items = l.xpath('list-item')
                    for j, lii in enumerate(items):
                        res = parse_citation(lii)
                        if res:
                            comment.append(res[0])
                            refs = res[1]
                        tr.append(t(lii, multi=True))
                    break

    return aw, gl, '\n'.join(tr), '; '.join(comment), refs


def iter_igt(d, abbrs):
    seen, count, number, letter = set(), 0, None, None
    lang, refs = None, []
    for gloss in element(d).xpath(".//list[@list-type='gloss']"):
        try:
            numbers = [
                t(li.xpath('list-item')[0])
                for li in gloss.xpath(".//list[@list-type='wordfirst']")]
        except IndexError:
            continue
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

        for ll in gloss.xpath("list-item/list[@list-type='sentence-gloss']"):
            if ll.xpath(".//list[@list-type='gloss']"):
                # there are nested examples! skip the wrapper.
                continue  # pragma: no cover
            # look for language and refs:
            fs = ll.xpath("list-item/list[@list-type='final-sentence']")
            if fs:
                items = fs[0].xpath('list-item')
                if items and len(items) == 1:
                    lname = parse_language_name(items[0])
                    if lname and len(lname) > 1 and lname[0].isupper():
                        lang = lname
                    for xref in items[0].xpath('p/xref'):
                        refs.append((xref.get('rid'), xref.get('ref-type'), xref.text))

            if ll.xpath("list-item/list[@list-type='word']") and not ll.xpath(".//inline-graphic"):
                try:
                    res = parse_igt(ll)
                except AssertionError:  # pragma: no cover
                    res = None
                if res:
                    igt = IGT(phrase=res[0], gloss=res[1], translation=res[2], abbrs=abbrs)
                    if igt.primary_text not in seen:
                        refs.extend(res[4])
                        count += 1
                        yield count, number, letter, lang, refs, igt, res[3]
                        seen.add(igt.primary_text)


def parse_language_name(e):
    e = element(e)
    n = None
    if e.xpath('p/italic'):
        if text(e.xpath('p')[0]).startswith('‘'):
            return
        n = e.xpath('p/italic')[0].text
    if e.xpath('p') and re.match(
            r'([A-Z][a-z]+)(\s+[A-Z][a-z]+)*\s+\(', e.xpath('p')[0].text or ''):
        n = e.xpath('p')[0].text.split('(')[0].strip()
    if e.xpath('p/sub') and not (e.xpath('p')[0].text or '').strip():
        n = text(e.xpath('p/sub')[0])
    if e.xpath('p/sc') and not (e.xpath('p')[0].text or '').strip():
        n = text(e.xpath('p/sc')[0])
    if n:
        return ' '.join(w.capitalize() for w in n.split())


def names(xp):
    res = []
    for n in xp:
        try:
            if not n.xpath('surname'):
                continue  # pragma: no cover
            name = n.xpath('surname')[0].text
            gn = n.xpath('given-names')
            if gn:
                name += ', {}'.format(gn[0].text)
            res.append(name)
        except:  # pragma: no cover # noqa: E722
            raise ValueError(tostring(n))  # pragma: no cover
    return ' and '.join(res)


def abbreviations(doc):
    sec = doc.xpath(".//sec[title/text()='Abbreviations']")
    res = {}
    if sec:
        ps = sec[0].xpath('p')
        if not ps:  # pragma: no cover
            return res
        abbr, desc = None, []
        for p in ps:
            for e in p.xpath('child::node()'):
                if getattr(e, 'tag', None):
                    if e.tag == 'sc' and e.text:
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
    title = re.sub(r'\s+', ' ', text(doc.xpath(".//article-title")[0]))
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


def parse_ref(ref):
    ref = element(ref)
    sid = ref.get('id')
    mixed = False
    try:
        ref = ref.xpath('element-citation')[0]
    except IndexError:
        mixed = True
        ref = ref.xpath('mixed-citation')[0]

    genre = {
        'journal': 'article',
        'confproc': 'inproceedings',
        'webpage': 'online',
        '/label': 'misc',
        'conf-proc': 'inproceedings',
        'cofproc': 'inproceedings',
    }.get(ref.get('publication-type'), ref.get('publication-type'))
    md = {}
    for pg in ref.xpath('person-group'):
        md[pg.get('person-group-type')] = names(pg.xpath('name'))
    if ref.xpath('string-name'):
        md['author'] = names(ref.xpath('string-name'))
    for year in ref.xpath('year'):
        md['year'] = year.text
        break
    for year in ref.xpath('edition'):
        md['edition'] = year.text
        break
    for uri in ref.xpath('uri'):
        md['url'] = uri.text
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
        md['title'] = text(p[0])
    p = ref.xpath("chapter-title")
    if p:
        genre = 'incollection'
        md['title'] = text(p[0])
    p = ref.xpath('source')
    if p:
        f = {
            'incollection': 'booktitle',
            'article': 'journal',
        }.get(genre, 'title')
        md[f] = text(p[0])
        if md[f].endswith('. doctoral dissertation'):
            md[f] = md[f].replace('. doctoral dissertation', '')
            genre = 'phdthesis'
    if mixed and '. doctoral dissertation' in text(ref, strict=False):
        genre = "phdthesis"
    if mixed and 'MA dissertation' in text(ref, strict=False):  # pragma: no cover
        genre = "mastersthesis"
    for xp, field in [
        ('conf-loc', 'address'),
        ('conf-name', 'howpublished'),
        ('conf-sponsor', 'publisher'),
        ('publisher-loc', 'address'),
        ('publisher-name', 'publisher'),
        ('volume', 'volume'),
        ('issue', 'number'),
        ('issn', 'issn'),
        ('isbn', 'isbn'),
    ]:
        p = ref.xpath(xp)
        if p:
            md[field] = text(p[0])

    if ('thesis' in genre) and ('publisher' in md):
        md['school'] = md.pop('publisher')

    return Source(genre, sid, **md)


def refs(doc):
    for ref in doc.xpath('.//ref-list/ref'):
        yield parse_ref(ref)
