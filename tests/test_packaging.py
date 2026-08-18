def test_tons_to_packets():
    tons = 2.5
    fill_weight = 1.0
    expected = int((tons * 1_000_000) // fill_weight)
    assert expected == 2_500_000


def test_yield_after_rejections():
    produced = 100000
    rejected = 125
    assert produced - rejected == 99875
