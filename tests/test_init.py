from linglit import iter_publications


def test_iter_publications(test_dir, glottolog_api):
    pubs = list(iter_publications(test_dir, glottolog=glottolog_api, with_examples=True))
    assert len(pubs) == 2
