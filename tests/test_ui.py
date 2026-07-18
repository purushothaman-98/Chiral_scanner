import pytest

from chiral_scanner.ui import paginate


def test_pagination():
    page, total, safe = paginate(list(range(45)), 2, 20)
    assert page == list(range(20, 40))
    assert total == 3
    assert safe == 2


def test_empty_pagination():
    page, total, safe = paginate([], 7, 20)
    assert page == [] and total == 1 and safe == 1


def test_invalid_page_size():
    with pytest.raises(ValueError):
        paginate([1], 1, 0)
