import pytest

from linglit.langsci.examples import *


def test_make_example(mocker):
    ex = make_example(
        mocker.Mock(), ('', '', ''), ['The phrase.', 'THE GLOSS', "The translation"], '')
    #assert ex.Gloss == ['THE', 'GLOSS']


@pytest.mark.parametrize(
    'lines,res',
    [
        (['a', 'b', '\\text{c}'], (['a', 'b'], 'c', None)),
        (['a', 'b', '[a comment]'], (['a', 'b'], 'a comment', None)),
        (['a\\jambox{cmt}', 'b', 'c'], (['a', 'b'], 'cmt; c', None)),
        (['a', 'b', '}{Lang}'], (['a', 'b'], '', ('Lang', '', ''))),
    ]
)
def test_lines_and_comment(lines, res):
    from linglit.langsci.examples import lines_and_comment

    assert lines_and_comment(lines) == res


def test_parse_langinfo():
    from linglit.langsci.examples import parse_langinfo

    assert parse_langinfo('\\langinfo{\\Language}{}{}') == ('\\Language', '', '')


def test_iter_gll():
    res = list(iter_gll('\\gll a\\\\b\n\\glt t'))
    assert res

    res = list(iter_gll("""
\\ili{LanguageA}
\\il{LanguageB}
\\ex Languagec \\citet{x} 
\\gll A\\\\
B
\\glt C
"""))
    assert len(res) == 1
    assert res[0][0][0] == 'Languagec'

    res = list(iter_gll(r"""
  \ea\label{x:rc-80}
\longexampleandlanguage{
  \gll   un problème dont     Paul est certain [[que nous avons parlé  \trace] [et que nous \textnobf{y} reviendrons plus tard]]\\
    a  problem  of.which Paul is  sure    \hphantom{[[}that we have   spoken {} \hphantom{[}and that we to.it will.come.back more late\\}{French}
  \glt Lit: `a problem of which Paul is sure that we have  spoken and that he is sure that we will come back to it later'
  \z
"""))
    assert res[0][0][0] == 'French'


def test_recombine():
    from linglit.langsci.examples import recombine

    assert list(recombine(['a', '', '-b'])) == ['a-b']


@pytest.mark.parametrize(
    'pt,gl,res',
    [
        ('a b .', 'A B', (['a', 'b.'], ['A', 'B'], None)),
        ('a b []', 'A B', (['a', 'b'], ['A', 'B'], None)),
        ('a b', 'A B [comment]', (['a', 'b'], ['A', 'B'], 'comment')),
        ('a b …', 'A B', (['a', 'b', '…'], ['A', 'B', '…'], None)),
        ('a b ∅', 'A B', (['a', 'b', '∅'], ['A', 'B', '∅'], None)),
        ('a b ∅.', 'A B', (['a', 'b', '∅.'], ['A', 'B', '∅'], None)),
        ('a b /', 'A B', (['a', 'b', '/'], ['A', 'B', '/'], None)),
        ('a b ]', 'A B', (['a', 'b', ']'], ['A', 'B', '_'], None)),
        ('a b (comment)', 'A B', (['a', 'b'], ['A', 'B'], 'comment')),
        ('… a b …', 'A B', (['…', 'a', 'b', '…'], ['…', 'A', 'B', '…'], None)),
        ('< a b >', 'A B', (['<', 'a', 'b', '>'], ['_', 'A', 'B', '_'], None)),
    ]
)
def test_fix_alignment(pt, gl, res):
    from linglit.langsci.examples import fixed_alignment

    assert fixed_alignment(pt, gl) == res
