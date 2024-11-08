
def test_iter_references(cldf_pub, cldf_pub2):
    assert len(list(cldf_pub.iter_references())) == 95
    assert len(list(cldf_pub2.iter_references())) == 1
    assert len(list(cldf_pub2.iter_cited())) == 1
    assert cldf_pub.record.as_source()['title'] == 'Uralic Typological database - UraTyp'
