import pytest

from linglit.langsci.catalog import Record, Catalog


def test_Record():
    rec = Record(
        ID='1',
        DOI='d',
        metalanguage='m',
        objectlanguage='o',
        license='l',
        creators='c,',
        title='t',
        edited='ed',
        superseded='True',
        pages=None,
        series='the series',
        seriesnumber='1',
        year='1999',
    )
    assert not rec.current
    assert str(rec.as_source())


def test_Catalog(mocker, test_dir, tmp_path):
    bcat = test_dir.joinpath('langsci', 'catalog.tsv').read_bytes()
    mocker.patch(
        'linglit.langsci.catalog.urllib.request',
        mocker.Mock(urlopen=lambda u: mocker.Mock(read=lambda: bcat)))
    cat = Catalog.from_remote()
    fname = tmp_path / 'test'
    cat.write(fname)
    cat = Catalog.from_local(fname)
    assert len(cat) == 1
    assert cat['1']

    with pytest.raises(KeyError):
        _ = cat['xyz']
