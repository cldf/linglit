import json
import base64
import shutil
import pathlib

import pytest
from clldutils import jsonlib

from linglit.langsci import Repository


@pytest.fixture
def repo():
    return Repository(pathlib.Path(__file__).parent / 'langsci')


@pytest.fixture
def tmp_repo(tmp_path):
    return Repository(tmp_path)


@pytest.mark.skipif(not shutil.which('bibtool'), reason="bibtool command not available.")
def test_Repository(repo):
    pubs = list(repo.iter_publications())
    assert len(pubs) == 1
    pub = pubs[0]
    assert len(pub.cited) == 1

    assert len(pub.examples) == 1
    assert pub.example_sources(pub.examples[0])[0].genre == 'book'
    assert repo['1']


def test_Repository_fetch_filelist(tmp_repo, mocker, langsci_repos):
    class Req:
        def urlopen(self, url):
            return mocker.Mock(read=lambda: langsci_repos.joinpath('catalog.tsv').read_bytes())

    mocker.patch('linglit.langsci.catalog.urllib.request', Req())
    tmp_repo.fetch_catalog()
    assert len(tmp_repo.catalog) == 1

    content = b'{"default_branch": "", "url": "", "tree": [{"path": "LSP", "mode": "", ' \
              b'"type": "blob", "sha": "", "url": ""}]}'
    mocker.patch('linglit.langsci.repository.ensure_cmd', lambda _: True)
    mocker.patch(
        'linglit.langsci.repository.subprocess',
        mocker.Mock(check_output=lambda *a, **kw: content))
    mocker.patch('linglit.langsci.repository.TEX_BRANCH', {1: 'main'})
    tmp_repo.fetch_filelist()
    tmp_repo.fetch_filelist()


def test_Repository_fetch_files(tmp_repo, mocker, tmp_path):
    content = b'abc'
    mocker.patch(
        'linglit.langsci.repository.subprocess',
        mocker.Mock(
            check_output=lambda *a, **kw: json.dumps(
                dict(content=base64.b64encode(content).decode(), encoding='base64'))))
    fl = tmp_repo.path('filelist.json')
    jsonlib.dump(dict({
        "16": [
            "main",
            {
                "sha": "d805fceec498820aa257377b5cd043b9390ea838",
                "url": "",
                "tree": [
                    {
                        "path": "main.tex",
                        "mode": "040000",
                        "type": "blob",
                        "sha": "90da271a89bfb92ccac0057f11b382ea62ce0507",
                        "url": "",
                        "size": 3,
                    }
                ]
            }]
    }), fl)
    tmp_repo.fetch_files(fl)
    assert tmp_repo.path('16', 'main.tex').exists()


def test_File(mocker, tmp_path):
    from linglit.langsci.repository import File

    content = b'abc'
    mocker.patch(
        'linglit.langsci.repository.subprocess',
        mocker.Mock(
            check_output=lambda *a, **kw: json.dumps(
                dict(content=base64.b64encode(content).decode(), encoding='base64'))))
    f = File(path='x', sha='x', mode='', type='blob', size=3, url='x')
    assert f.content == content

    f.save(tmp_path)
    assert f.same_content(tmp_path / 'x')
    assert f.same_content(tmp_path / 'x', shallow=False)


def test_branch_and_tree(mocker):
    from linglit.langsci.repository import branch_and_tree

    mocker.patch(
        'linglit.langsci.repository.subprocess',
        mocker.Mock(check_output=lambda *a, **kw: json.dumps(dict(default_branch='main'))))

    res = branch_and_tree('3', None)
    assert res[0] == 'main'
