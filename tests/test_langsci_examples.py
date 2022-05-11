from linglit.langsci.examples import *


def test_iter_gll():
    res = list(iter_gll('\\gll a\\\\b\n\\glt t'))
    assert res


def test_make_example(mocker):
    ex = make_example(
        mocker.Mock(), ('', '', ''), ['The phrase.', 'THE GLOSS', "The translation"], '')
    #assert ex.Gloss == ['THE', 'GLOSS']


def test_lines_and_comment():
    from linglit.langsci.examples import lines_and_comment

    assert lines_and_comment(['a', 'b', '\\text{c}']) == (['a', 'b'], 'c', None)
    assert lines_and_comment(['a', 'b', '[a comment]']) == (['a', 'b'], 'a comment', None)
    #assert lines_and_comment(['a', 'b', '(Proto-English)']) == (['a', 'b'], '', ('Proto-English', '', ''))
    assert lines_and_comment(['a\\jambox{cmt}', 'b', 'c']) == (['a', 'b'], 'cmt; c', None)
    assert lines_and_comment(['a', 'b', '}{Lang}']) == (['a', 'b'], '', ('Lang', '', ''))
