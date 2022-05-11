import pathlib

import pytest


@pytest.fixture
def test_dir():
    return pathlib.Path(__file__).parent


@pytest.fixture
def glossa_repos(test_dir):
    return test_dir / 'glossa'
