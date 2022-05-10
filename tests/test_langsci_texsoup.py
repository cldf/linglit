from linglit.langsci.texsoup import iter_texsoup_lines

def test_iter_texsoup_lines():
    lines = list(iter_texsoup_lines(None, tex='abc\n\\cite{abc}'))
    print(lines)
    assert lines[1].cite.string == 'abc'
