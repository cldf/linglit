import pytest

from linglit.langsci.texfixes import normalize_cite


@pytest.mark.parametrize(
    'tex,normalized',
    [
        (r'\citeplain*[2]{a}', r'\cite[2]{a}'),
    ]
)
def test_normalize_cite(tex, normalized):
    assert normalize_cite(tex) == normalized
