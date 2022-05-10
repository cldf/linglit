import pathlib

import pytest

from linglit.glossa import Repository


@pytest.fixture
def repo():
    return Repository(pathlib.Path(__file__).parent / 'glossa')


def test_Repository_examples(repo):
    pub = list(repo.iter_publications())[0]
    assert str(pub.as_source()) == \
           'Skilton, Amalia and Obert, Karolin. 2022. Differential place marking beyond place ' \
           'names: Evidence from two Amazonian languages. Glossa: a journal of general ' \
           'linguistics 7(1). Open Library of Humanities.'
    assert pub.record.has_open_license
    assert len(pub.references) == 33
    assert len(pub.cited_references) == 33
    assert len(pub.examples) == 42
    assert pub.examples[3].Language_Name == 'daww1239'
    assert pub.examples[0].Comment == 'Pseudo-stripping'
