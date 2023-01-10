import os

import pytest

from linglit import iter_publications


@pytest.mark.skipif('CI' in os.environ, reason="bibtool command not available in GH action.")
def test_iter_publications(test_dir, glottolog_api):
    pubs = list(iter_publications(test_dir, glottolog=glottolog_api, with_examples=True))
    assert len(pubs) == 4
