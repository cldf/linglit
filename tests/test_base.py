from linglit.base import Glottolog


def test_Glottolog(glottolog_api):
    gl = Glottolog(glottolog_api)
    gl.register_names({'aka': 'abcd1234'})
    assert gl('abcd1234') == 'abcd1234'
    assert gl('aka') == 'abcd1234'
    assert gl('alias') == 'abcd1234'
    assert gl('lang') == 'abcd1234'
    assert gl('abc') == 'abcd1234'
    assert gl('xyz') is None