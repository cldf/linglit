import pytest

from linglit.glossa import Repository


@pytest.fixture
def repo(glossa_repos):
    return Repository(glossa_repos)


def test_Repository_examples(repo):
    pub = repo['6371']
    assert str(pub.as_source()).startswith('Skilton, Amalia')
    assert pub.record.has_open_license
    assert len(pub.references) == 33
    assert len(pub.cited_references) == 33
    assert len(pub.examples) == 42
    assert pub.examples[3].Language_Name == 'daww1239'
    assert pub.examples[0].Comment == 'Pseudo-stripping'

    with pytest.raises(KeyError):
        _ = repo['unknown']

    assert len(repo['5703'].examples) == 32

    assert [ex.Local_ID for ex in repo['5887'].examples[:10]] == \
           ['1a', '1b', '1c', '1d', '1d', '1d', '1e', '1e', '2a', '2b']


def test_Repository_create(tmp_path, mocker, glossa_repos, capsys):
    class Req:
        def urlopen(self, url):
            return mocker.Mock(read=lambda: glossa_repos.joinpath('articles.html').read_bytes())

    mocker.patch('linglit.glossa.repository.urllib.request', Req())
    repo = Repository(tmp_path)
    repo.create(verbose=True)
    out, _ = capsys.readouterr()
    assert 'retrieving' in out
