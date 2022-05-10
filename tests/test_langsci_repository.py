import pathlib

import pytest

from linglit.langsci import Repository


@pytest.fixture
def repo():
    return Repository(pathlib.Path(__file__).parent / 'langsci')


def test_Repository(repo):
    pubs = list(repo.iter_publications())
    assert len(pubs) == 1
    pub = pubs[0]
    assert len(pub.cited) == 1

    assert len(pub.examples) == 1
    assert pub.example_sources(pub.examples[0])[0].genre == 'book'
