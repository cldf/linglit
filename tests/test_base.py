from linglit.base import Glottolog, Example


def test_Glottolog(glottolog_api):
    gl = Glottolog(glottolog_api)
    gl.register_names({'aka': 'abcd1234'})
    assert gl('abcd1234') == 'abcd1234'
    assert gl('aka') == 'abcd1234'
    assert gl('alias') == 'abcd1234'
    assert gl('lang') == 'abcd1234'
    assert gl('abc') == 'abcd1234'
    assert gl('xyz') is None


def test_Publication(glossa_pub):
    assert glossa_pub.is_current and glossa_pub.has_open_license
    assert 'Skilton' in str(glossa_pub)


def test_Example():
    ex = Example(
        ID=1,
        Primary_Text='text',
        Analyzed_Word=[],
        Gloss=[],
        Translated_Text='some text [and a comment]',
        Language_Name='l',
        Comment='comment',
        Source=[])
    assert ex.Comment == 'comment; and a comment'
