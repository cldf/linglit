from linglit.langsci.examples import *


def test_iter_gll():
    res = list(iter_gll('\\gll a\\\\b\n\\glt t'))
    assert res


def test_make_example(mocker):
    ex = make_example(
        mocker.Mock(), ('', '', ''), ['The phrase.', 'THE GLOSS', "The translation"], '')
    #assert ex.Gloss == ['THE', 'GLOSS']
