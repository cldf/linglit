import re
import typing
import pathlib
import collections

from clldutils.misc import slug
from pybtex import database
from pycldf.sources import Source
from thefuzz import fuzz
from unidecode import unidecode

__all__ = ['iter_merged', 'iter_entries']

YEAR_PATTERN = re.compile('([0-9]{4})')
ACC_FIELDS = {  # Fields where content from merged records should be accumulated.
    'isreferencedby': ' ',
}


def hash(e):
    creators = e.persons.get('author') or e.persons.get('editor')
    year = YEAR_PATTERN.search(e.fields.get('year') or '')
    return (
        slug(e.fields.get('title') or ''),
        year.groups()[0] if year else '',
        slug(''.join(creators[0].last_names)) if creators else ''
    )


def similarity(s1, s2):
    return max([fuzz.ratio(s1, s2), fuzz.token_set_ratio(s1, s2)])


def iter_entries(
        d: typing.Union[str, pathlib.Path]) -> typing.Generator[database.Entry, None, None]:
    d = pathlib.Path(d)
    for p in sorted(d.glob('*.bib'), key=lambda pp: pp.stem):
        yield from database.parse_string(p.read_text(encoding='utf8'), 'bibtex').entries.values()


def iter_merged(
        entries: typing.Iterable[typing.Union[Source, database.Entry]]
) -> typing.Generator[typing.Tuple[Source, dict], None, None]:
    """
    We merge in a multi-step procedure.

    1. We compute a hash based on creators, year and title for each entry, and aggregate entries
       with matching hash.
    2. We compute a citation key based on creators and year, and if entries with different hashes
       get the same key, we examine the titles using fuzzy comparison.
    3. The final citation key is created from the provisional keys by appending a number for
       disambiguation.
    """
    aggr = collections.defaultdict(list)
    for e in entries:
        if isinstance(e, Source):
            sid = e.id
            e = e.entry
            e.key = sid
        aggr[hash(e)].append(e)

    keys = {}
    by_key = collections.defaultdict(list)

    def norm_title(e):
        return e.fields.get('title', '').lower()

    for h, v in sorted(aggr.items()):
        t, y, a = h
        if t and (y or a):  # A meaningful has. So we assume all entries in v to be identical.
            k = make_key(v[0])
            if k in keys:  # The same key has already been computed for a batch of entries.
                (_, y2, a2), title2 = keys[k]
                title = norm_title(v[0])

                sim = 0
                if y == y2 and a == a2 and title and title2:
                    sim = similarity(title, title2)

                if sim >= 92:  # Just a threshold ...
                    # identify with the previous batch under this key!
                    by_key[k][-1].extend(v)
                else:
                    # Otherwise, just add a new batch for the key:
                    by_key[k].append(v)
            else:
                by_key[k].append(v)
            keys[k] = h, norm_title(v[0])
        else:  # not enough information to actually identify records!
            for e in v:
                k = make_key(e)
                by_key[k].append([e])

    for k, batches in sorted(by_key.items(), key=lambda i: i[0]):
        if len(batches) == 1:
            yield merged(k, batches[0])
        else:
            for i, batch in enumerate(batches, start=1):
                yield merged('{}:{}'.format(k, i), batch)


def merged(key, batch):
    m, keymap = None, {}
    for i, e in enumerate(batch):
        keymap[e.key] = key
        if i == 0:
            m = Source.from_entry(key, e)
        else:
            for k, v in e.fields.items():
                if not v.strip():  # pragma: no cover
                    continue
                if k in ACC_FIELDS:
                    if k in m:
                        m[k] += '{}{}'.format(ACC_FIELDS[k], v)
                    else:
                        m[k] = v
                else:
                    if k not in m or len(m[k]) < len(v):  # longest is best
                        m[k] = v
    m['citekeys'] = ' '.join(sorted(keymap))
    return m, keymap


def make_key(e):
    ed = ''
    creators = e.persons.get('author')
    if not creators:
        creators = e.persons.get('editor')
        if creators:
            ed = ':ed'
    if creators:
        s = ''
        for i, p in enumerate(creators, start=1):
            if i > 2:
                s += ':etal'
                break
            s += (':' if s else '') + ''.join(p.prelast_names + p.last_names)
    else:
        s = 'np'
    year = YEAR_PATTERN.search(e.fields.get('year') or '')
    if year:
        year = year.groups()[0][2:]
    else:
        year = 'nd'
    s = s.replace("ä", "ae")
    s = s.replace("ö", "oe")
    s = s.replace("ü", "ue")
    s = s.replace('"=', '-')
    creators = unidecode(s)
    for c in "/.'()= ":
        creators = creators.replace(c, '')
    return creators.lower() + ed + ':' + year


# --------------------------------------
def main():  # pragma: no cover
    def read_bib(p):
        return {k: e for k, e in
                database.parse_string(p.read_text(encoding='utf8'), 'bibtex').entries.items()}

    lsp = pathlib.Path('lsp.bib')
    lsp.write_text('\n\n'.join(
        [m[0].bibtex() for m in iter_merged(iter_entries('langsci/bibtex'))]), encoding='utf8')

    #
    # compare citation keys between langsci.bib and lsp.bib
    #
    gllsp = read_bib(pathlib.Path('../../glottolog/glottolog/references/bibtex/langsci.bib'))
    lsp = read_bib(lsp)
    lspkeys = {re.sub(':[0-9]$', '', k) for k in lsp}
    lsp_no_ed_keys = {k.replace(':ed:', ':') for k in lspkeys}

    a, m = 0, 0
    for k in gllsp:
        k = re.sub('([0-9])[a-z]$', lambda m: m.groups()[0], k)
        a += 1
        if k.lower() not in lspkeys:
            kk = k.lower().replace(':ed:', ':')
            if kk not in lsp_no_ed_keys:
                m += 1
                print(k)
    print(a, m)
