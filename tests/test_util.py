import pytest

from linglit.util import clean_translation


@pytest.mark.parametrize(
    'tr,res',
    [
        ("`abc'", 'abc'),
        ("`abc'.", 'abc.'),
        ("", ""),
    ]
)
def test_clean_translation(tr, res):
    assert clean_translation(tr) == res
