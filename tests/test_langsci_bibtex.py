import pytest

from linglit.langsci.bibtex import LangsciSource, to_source


@pytest.mark.parametrize(
    'genre,md,test',
    [
        ('misc', dict(title='a(b'), lambda s: s['title'] == 'ab'),
        ('phdthesis', dict(type='M.A.'), lambda s: s.genre == 'mastersthesis'),
        ('misc', dict(xmonth='May'), lambda s: 'xmonth' not in s),
        ('misc', dict(journaltitle='a'), lambda s: 'journal' in s and 'journaltitle' not in s),
    ]
)
def test_to_source(genre, md, test):
    assert test(to_source('x', LangsciSource(genre, 'x', **md)))
