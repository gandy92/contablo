import datetime
from decimal import Decimal

import pytest

from contablo.fields import DecimalFieldSpec
from contablo.fields import StringFieldSpec
from contablo.importable import ImporTable
from contablo.importable import ImportDatum

from .defs_fields import financial_transaction_fields


def test_importable_iter_data():
    dut = ImporTable(financial_transaction_fields)
    dut.data_vector = [1, 2, 3]

    assert list(dut.iter_data(reversed=False)) == [1, 2, 3]
    assert list(dut.iter_data(reversed=True)) == [3, 2, 1]


def datum(value: str, fmt: str = "") -> ImportDatum:
    return ImportDatum(source_lbl="col", raw_value=value, format=fmt)


def test_importable_add_converts_values():
    dut = ImporTable(financial_transaction_fields)
    dut.add("src:1", {"tx_date": datum("01.02.2023", "dd.mm.yyyy"), "quote_amount": datum("1.234,50", "1.000,00")})
    assert dut.data_vector == [
        {"imported_from": "src:1", "tx_date": datetime.date(2023, 2, 1), "quote_amount": Decimal("1234.50")}
    ]


def test_importable_add_skips_rows_with_drop():
    dut = ImporTable(financial_transaction_fields)
    dut.add("src:1", {"drop": datum("drop"), "note": datum("x")})
    assert len(dut) == 0


def test_importable_add_reports_unknown_fields_without_raising(capsys):
    dut = ImporTable(financial_transaction_fields)
    dut.add("src:1", {"unknown_field": datum("x")})
    assert "Unknown field <unknown_field>" in capsys.readouterr().out
    assert len(dut) == 0


def test_importable_add_raises_on_conversion_error(capsys):
    dut = ImporTable(financial_transaction_fields)
    with pytest.raises(ImportError):
        dut.add("src:1", {"tx_type": datum("NOT_A_TX_TYPE")})
    assert len(dut) == 0


def test_importable_clone_empty_drops_data_and_extra_fields():
    dut = ImporTable(financial_transaction_fields)
    dut.add_extra_fields([DecimalFieldSpec("extra", "extra field")])
    dut.data_vector = [{"note": "x"}]
    clone = dut.clone_empty()
    assert len(clone) == 0
    assert clone.columns == dut.export_columns
    assert "extra" in dut.columns


def test_importable_get_flat_table_and_get_data():
    dut = ImporTable([StringFieldSpec("a", ""), DecimalFieldSpec("b", "")])
    dut.data_vector = [{"a": "x", "b": Decimal("1.50"), "imported_from": "src:1"}, {"a": "y"}]
    assert dut.get_flat_table(convert_func=str, fallback="", include_header=True) == [
        ["a", "b"],
        ["x", "1.50"],
        ["y", ""],
    ]
    assert dut.get_flat_table() == [["x", Decimal("1.50")], ["y", None]]
    data = dut.get_data()
    assert data == dut.data_vector and data[0] is not dut.data_vector[0]
    assert dut.get_columns() == ["a", "b"]


def test_importable_compatible_fields():
    dut = ImporTable([StringFieldSpec("a", ""), DecimalFieldSpec("b", ""), DecimalFieldSpec("c", "")])
    assert dut.compatible_fields("a") == ["a"]
    assert dut.compatible_fields("number") == ["b", "c"]
    assert dut.compatible_fields("date") == []


def test_importable_merge_in_skips_known_entries():
    dut = ImporTable([StringFieldSpec("a", "")])
    dut.data_vector = [{"a": "x", "imported_from": "f1:1"}]
    other = dut.clone_empty()
    other.data_vector = [{"a": "x", "imported_from": "f2:1"}, {"a": "y", "imported_from": "f2:2"}]
    dut.merge_in(other)
    assert dut.data_vector == [{"a": "x", "imported_from": "f1:1"}, {"a": "y", "imported_from": "f2:2"}]
