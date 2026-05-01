import dataclasses
import shutil

from linglit.cldf import Repository


def test_create(tmp_path, cldf_repos, mocker):
    @dataclasses.dataclass
    class ZenodoRecord:
        version: str = '1.0'

        @classmethod
        def from_concept_doi(cls, _):
            return cls()

        def download_dataset(self, d):
            d.mkdir(parents=True, exist_ok=True)

    shutil.copy(cldf_repos / 'catalog.csv', tmp_path)
    repo = Repository(tmp_path)

    mocker.patch('linglit.cldf.repository.cldfzenodo', mocker.Mock(Record=ZenodoRecord()))
    repo.create()
    repo.create()
