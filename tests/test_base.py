from pyglottolog.languoids import Languoid

from linglit.base import Glottolog


def test_Glottolog(mocker, tmp_path):
    class API:
        def languoids(self):
            lg = Languoid.from_name_id_level(tmp_path, 'lang', 'abcd1234', 'language', iso='abc')
            lg.add_name('alias')
            yield lg

    mocker.patch('linglit.base.API', API)
    gl = Glottolog(API())
    gl.register_names({'aka': 'abcd1234'})
    assert gl('abcd1234') == 'abcd1234'
    assert gl('aka') == 'abcd1234'
    assert gl('alias') == 'abcd1234'
    assert gl('lang') == 'abcd1234'
    assert gl('abc') == 'abcd1234'
    assert gl('xyz') is None