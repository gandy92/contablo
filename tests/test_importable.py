from contablo.importable import ImporTable

from .defs_fields import financial_transaction_fields


def test_importable_iter_data():
    dut = ImporTable(financial_transaction_fields)
    dut.data_vector = [1, 2, 3]

    assert list(dut.iter_data(reversed=False)) == [1, 2, 3]
    assert list(dut.iter_data(reversed=True)) == [3, 2, 1]
