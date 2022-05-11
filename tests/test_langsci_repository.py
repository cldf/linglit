import json
import base64
import pathlib

import pytest
from clldutils import jsonlib

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


def test_Repository_fetch_files(tmp_path, mocker):
    content = b'abc'
    mocker.patch(
        'linglit.langsci.repository.subprocess',
        mocker.Mock(
            check_output=lambda *a, **kw: json.dumps(
                dict(content=base64.b64encode(content).decode(), encoding='base64'))))
    fl = tmp_path / 'filelist.json'
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
    repo = Repository(tmp_path)
    repo.fetch_files(fl)
    assert tmp_path.joinpath('16', 'main.tex').exists()


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
