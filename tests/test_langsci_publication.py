import shutil

from linglit.langsci.publication import Publication


def test_Publication_main(tmp_path, mocker):
    tmp_path.joinpath('Makefile').write_text('\nxelatex the\n', encoding='utf8')
    tmp_path.joinpath('the.tex').write_text('\\yes{}')
    assert Publication(mocker.Mock(), tmp_path).main.name == 'the.tex'

    tmp_path.joinpath('Makefile').write_text('\nmake  the.pdf \n', encoding='utf8')
    assert Publication(mocker.Mock(), tmp_path).main.name == 'the.tex'

    tmp_path.joinpath('Makefile').write_text('\n\n', encoding='utf8')
    tmp_path.joinpath('the.tex').unlink()
    tmp_path.joinpath('nested').mkdir()
    tmp_path.joinpath('nested', 'main.tex').write_text('\\yes{}')
    assert Publication(mocker.Mock(), tmp_path).main.parent.name == 'nested'

    tmp_path.joinpath('nested', 'main.tex').unlink()
    tmp_path.joinpath('theother.tex').write_text('\\documentclass{number=1}\n')
    assert Publication(mocker.Mock(), tmp_path).main.name == 'theother.tex'

    shutil.move(str(tmp_path / 'theother.tex'), str(tmp_path / 'nested'))
    assert Publication(mocker.Mock(), tmp_path).main.parent.name == 'nested'

    shutil.move(str(tmp_path / 'Makefile'), str(tmp_path / 'nested'))
    assert Publication(mocker.Mock(), tmp_path).main.parent.name == 'nested'
