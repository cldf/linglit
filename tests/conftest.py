import pathlib

import pytest
from pyglottolog.languoids import Languoid


@pytest.fixture
def glottolog_api(mocker, tmp_path):
    class API:
        def languoids(self):
            lg = Languoid.from_name_id_level(tmp_path, 'lang', 'abcd1234', 'language', iso='abc')
            lg.add_name('alias')
            yield lg

    mocker.patch('linglit.base.API', API)
    return API()


@pytest.fixture
def test_dir():
    return pathlib.Path(__file__).parent


@pytest.fixture
def langsci_repos(test_dir):
    return test_dir / 'langsci'


@pytest.fixture
def langsci_pub121(langsci_repos):
    from linglit.langsci import Repository

    return Repository(langsci_repos)['121']


@pytest.fixture
def langsci_pub1(langsci_repos):
    from linglit.langsci import Repository

    return Repository(langsci_repos)['1']


@pytest.fixture
def glossa_repos(test_dir):
    return test_dir / 'glossa'


@pytest.fixture
def glossa_pub(glossa_repos):
    from linglit.glossa import Repository

    return Repository(glossa_repos)['6371']


@pytest.fixture
def cldf_repos(test_dir):
    return test_dir / 'cldf'


@pytest.fixture
def cldf_pub(cldf_repos):
    from linglit.cldf import Repository

    return Repository(cldf_repos)['uratyp']


@pytest.fixture
def cldf_pub2(cldf_repos):
    from linglit.cldf import Repository

    return Repository(cldf_repos)['petersonsouthasia']
