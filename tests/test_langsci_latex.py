from linglit.langsci.latex import to_text, strip_tex_comment


def test_to_text():
    assert to_text('\\tss{a}')[0] == '.A'
    assert to_text('\\footnote{text}')[1] == 'text'
    assert 'https://doi.org/10.24397/pangloss' in to_text('\\japhdoi{doi}')[0]
    assert to_text('\\jambox{}{b}')[0] == 'b'
    assert to_text('\\ref{a}{b}')[0] == 'ab'
    assert to_text('\\ref')[0] == ''
    assert to_text('\\linieb{a}{b}')[0] == 'b'
    assert to_text('\\japhug{a}{b}')[0] == 'a [b]'
    assert to_text('\\href{a}{b}')[0] == '[b](a)'
    assert to_text('\\scite{a}{b}')[2][0][0] == 'b'
    assert to_text('\\fatcit{a}{b}')[2][0] == ('a', 'b')


def test_strip_tex_comment():
    assert strip_tex_comment('a\\\\%b') == 'a\\\\'
