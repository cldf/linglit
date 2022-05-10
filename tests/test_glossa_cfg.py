from linglit.glossa.cfg import LanguageSpec


def test_LanguageSpec():
    lspec = LanguageSpec('abcd1234')
    assert lspec('name', None) == 'name'
    assert lspec(None, None) == 'abcd1234'
