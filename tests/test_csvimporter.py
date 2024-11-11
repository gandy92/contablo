import datetime
from decimal import Decimal

import pytest

from contablo.csvimporter import ImportSpecExceededError
from contablo.csvimporter import add_to_importable_using_import_spec
from contablo.importable import ImporTable
from tests.defs_importspec import import_spec_dict_acct1_account
from tests.defs_importspec import import_spec_dict_with_map
from tests.defs_importspec import import_spec_dict_with_map_and_match
from tests.defs_importspec import import_spec_inst1_sub1_with_implicit

from .defs_fields import financial_transaction_fields


def test_add_to_importable_using_import_spec():
    imp = ImporTable(financial_transaction_fields)
    input_1 = ["01.11.2021", "1,00", "bekannt", "ee17....d289"]
    add_to_importable_using_import_spec(imp, import_spec_dict_acct1_account, input_1, "test:1")
    assert imp.data_vector == [
        {
            "imported_from": "acct2:test:1",
            "quote_currency": "EUR",
            "tx_date": datetime.date(2021, 11, 1),
            "quote_amount+fees": Decimal("1.00"),
            "note": "bekannt",
            "reference": "ee17....d289",
            "tx_type": "DEPOSIT",
        }
    ]


def test_add_to_importable_using_import_spec_match_known():
    imp = ImporTable(financial_transaction_fields)
    input_1 = [
        "01.11.2021",
        "1,00",
        "Kauf WP-Kenn-Nr.: 886053, Intuit Inc., Nominale:  4,0000",
        "ee17....d289",
    ]
    add_to_importable_using_import_spec(imp, import_spec_dict_acct1_account, input_1, "test:1")
    assert imp.data_vector == [
        {
            "imported_from": "acct2:test:1",
            "quote_currency": "EUR",
            "tx_date": datetime.date(2021, 11, 1),
            "quote_amount+fees": Decimal("1.00"),
            "note": "Kauf WP-Kenn-Nr.: 886053, Intuit Inc., Nominale:  4,0000",
            "reference": "ee17....d289",
            "tx_type": "BUY",
            "asset_amount": Decimal("4.0000"),
            "wkn": "886053",
        }
    ]


def test_add_to_importable_using_import_spec_match_unknown():
    imp = ImporTable(financial_transaction_fields)
    input_1 = [
        "01.11.2021",
        "1,00",
        "Vormerkung Kauf Kennung: 886053, Intuit Inc., Nominale:  4,0000",
        "ee17....d289",
    ]
    with pytest.raises(ImportSpecExceededError):
        add_to_importable_using_import_spec(imp, import_spec_dict_acct1_account, input_1, "test:1")


def test_add_to_importable_using_import_spec_with_map():
    imp = ImporTable(financial_transaction_fields)
    input_1 = ["01.11.2021", "1,00", "Kauf", "ee17....d289"]
    add_to_importable_using_import_spec(imp, import_spec_dict_with_map, input_1, "test:1")
    assert imp.data_vector == [
        {
            "imported_from": "acct2:test:1",
            "quote_currency": "EUR",
            "tx_date": datetime.date(2021, 11, 1),
            "quote_amount+fees": Decimal("1.00"),
            "reference": "ee17....d289",
            "tx_type": "BUY",
        }
    ]


def test_add_to_importable_using_import_spec_with_map_and_match():
    imp = ImporTable(financial_transaction_fields)
    input_1 = ["01.11.2021", "1,00", "Kauf", "ee17....d289"]
    add_to_importable_using_import_spec(imp, import_spec_dict_with_map_and_match, input_1, "test:1")
    assert imp.data_vector == [
        {
            "imported_from": "acct2:test:1",
            "quote_currency": "EUR",
            "tx_date": datetime.date(2021, 11, 1),
            "quote_amount+fees": Decimal("1.00"),
            "reference": "ee17....d289",
            "tx_type": "BUY",
        }
    ]


def test_add_to_importable_using_import_spec_with_implicit_1():
    imp = ImporTable(financial_transaction_fields)

    inputs = [
        ["554122933", "2021-01-17 21:13:39", "Sub1", "Buy", "ASSET5", "41.00000000", ""],
        ["554122933", "2021-01-17 21:13:39", "Sub1", "Buy", "ASSET4", "-16.09250000", ""],
        ["554122933", "2021-01-17 21:13:39", "Sub1", "Fee", "ASSET5", "-0.04100000", ""],
    ]
    for idx, inp in enumerate(inputs, 1):
        add_to_importable_using_import_spec(imp, import_spec_inst1_sub1_with_implicit, inp, f"test:{idx}")

    assert imp.data_vector == [
        {
            "imported_from": "acct1-sub1:test:1",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2021, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "asset_amount": Decimal("41.00000000"),
            "asset_currency": "ASSET5",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:2",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2021, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-16.09250000"),
            "quote_currency": "ASSET4",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:3",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2021, 1, 17, 21, 13, 39),
            "fee_amount": Decimal("-0.04100000"),
            "fee_currency": "ASSET5",
            "_allow_add": True,
        },
    ]


def test_add_to_importable_using_import_spec_with_implicit_2():
    imp = ImporTable(financial_transaction_fields)

    inputs = [
        ["554122933", "2021-01-23 15:33:20", "Sub1", "Buy ", "ASSET3", "24.90000000", ""],
        ["554122933", "2021-01-23 15:33:20", "Sub1", "Buy ", "ASSET1", "-43.27620000", ""],
        ["554122933", "2021-01-25 00:01:28", "Sub1", "Sell", "ASSET1", "41.90670000", ""],
        ["554122933", "2021-01-25 00:01:28", "Sub1", "Sell", "ASSET3", "-24.90000000", ""],
    ]
    for idx, inp in enumerate(inputs, 1):
        add_to_importable_using_import_spec(imp, import_spec_inst1_sub1_with_implicit, inp, f"test:{idx}")

    assert imp.data_vector == [
        {
            "imported_from": "acct1-sub1:test:1",
            "tx_reference": "acct1-554122933-Sub1-2021-01-23 15:33:20",
            "tx_datetime": datetime.datetime(2021, 1, 23, 15, 33, 20),
            "tx_type": "SWAP",
            "asset_amount": Decimal("24.90000000"),
            "asset_currency": "ASSET3",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:2",
            "tx_reference": "acct1-554122933-Sub1-2021-01-23 15:33:20",
            "tx_datetime": datetime.datetime(2021, 1, 23, 15, 33, 20),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-43.27620000"),
            "quote_currency": "ASSET1",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:3",
            "tx_reference": "acct1-554122933-Sub1-2021-01-25 00:01:28",
            "tx_datetime": datetime.datetime(2021, 1, 25, 0, 1, 28),
            "tx_type": "SWAP",
            "quote_amount": Decimal("41.90670000"),
            "quote_currency": "ASSET1",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:4",
            "tx_reference": "acct1-554122933-Sub1-2021-01-25 00:01:28",
            "tx_datetime": datetime.datetime(2021, 1, 25, 0, 1, 28),
            "tx_type": "SWAP",
            "asset_amount": Decimal("-24.90000000"),
            "asset_currency": "ASSET3",
            "_allow_add": True,
        },
    ]


def test_add_to_importable_using_import_spec_with_implicit_3():
    imp = ImporTable(financial_transaction_fields)

    inputs = [
        ["554122933", "2021-01-17 02:02:32", "Sub1", "Buy", "ASSET4", "-15.37900000", ""],
        ["554122933", "2021-01-17 02:02:32", "Sub1", "Buy", "ASSET0", "0.91000000", ""],
        ["554122933", "2021-01-17 02:02:32", "Sub1", "Referral Kickback", "ASSET0", "0.00009100", ""],
        ["554122933", "2021-01-17 02:02:32", "Sub1", "Fee", "ASSET0", "-0.00091000", ""],
    ]
    for idx, inp in enumerate(inputs, 1):
        add_to_importable_using_import_spec(imp, import_spec_inst1_sub1_with_implicit, inp, f"test:{idx}")

    assert imp.data_vector == [
        {
            "imported_from": "acct1-sub1:test:1",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2021, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-15.37900000"),
            "quote_currency": "ASSET4",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:2",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2021, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "asset_amount": Decimal("0.91000000"),
            "asset_currency": "ASSET0",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:3",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2021, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "refund_amount": Decimal("0.00009100"),
            "refund_currency": "ASSET0",
            "_allow_add": True,
        },
        {
            "imported_from": "acct1-sub1:test:4",
            "tx_reference": "acct1-554122933-Sub1-2021-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2021, 1, 17, 2, 2, 32),
            "fee_amount": Decimal("-0.00091000"),
            "fee_currency": "ASSET0",
            "_allow_add": True,
        },
    ]
