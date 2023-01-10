import logging

from linglit.__main__ import main


def test_bib(capsys, glossa_repos):
    main(['bib', 'glossa', str(glossa_repos), '6371'], log=logging.getLogger(__name__))
    out, _ = capsys.readouterr()
    assert 'Ameka, Felix' in out


def test_igt(capsys, glossa_repos):
    main(['igt', 'glossa', str(glossa_repos), '6371'])
    out, _ = capsys.readouterr()
    assert 'daww1239' in out


def test_mergedbib(capsys, glossa_repos):
    main(['mergedbib', 'glossa', str(glossa_repos)])
    out, _ = capsys.readouterr()
    assert 'isreferencedby' in out
    assert ':j,ed' not in out
