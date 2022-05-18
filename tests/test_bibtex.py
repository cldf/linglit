import copy

from pycldf.sources import Source

from linglit.bibtex import *


def test_merge(tmp_path, langsci_repos):
    assert merge(langsci_repos / '1', tmp_path / 'out.bib') == 2


def test_iter_merged():
    # Same hash:
    md = dict(editor="Author, The and B, C and D, E", year="1999", title="This is the Title")
    res = list(iter_merged([Source('misc', 's1', **md), Source('misc', 's2', isreferencedby='a', **md)]))
    assert len(res) == 1
    assert len(res[0][1]) == 2
    assert 's2' in res[0][0]['citekeys']

    # Different hash, same key:
    src1 = Source('misc', 's1', isreferencedby='a', **copy.copy(md))
    md['title'] += ' More'
    res = list(iter_merged([src1, Source('misc', 's2', x='', isreferencedby='c', **md)]))
    assert len(res) == 1
    assert res[0][0]['isreferencedby'] == 'a c'
    assert 'x' not in res[0][0]

    # Different hash, same key but "different enough" title:
    md['title'] = "This is the Titlestring"
    res = list(iter_merged([src1, Source('misc', 's2', **md)]))
    assert len(res) == 2

    # Not enough info to create a meaningful hash:
    del md['editor']
    del md['year']
    res = list(iter_merged([Source('misc', 's1', **md), Source('misc', 's2', **md)]))
    assert len(res) == 2


def test_iter_entries(langsci_repos, tmp_path):
    assert len(list(iter_entries(langsci_repos / '1'))) == 3

    tmp_path.joinpath('test.bib').write_text(
        '@article{key,\ntitle={{Word} in {Braces}},\nseries={\\href{..}}}', encoding='utf8')
    res = list(iter_entries(tmp_path / 'test.bib', delatex=True))
    assert len(res) == 1
    assert res[0].fields['title'] == 'Word in Braces'
    assert res[0].fields['series'] == '\\href{..}'
