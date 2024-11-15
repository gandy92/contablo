import datetime
from decimal import Decimal

import pytest

from contablo.importable import ImporTable
from contablo.importablemerge import dicts_match_by_map
from contablo.importablemerge import importable_merge_one
from contablo.importablemerge import importable_merge_two
from contablo.importablemerge import pick_one

from .defs_fields import addable_fields
from .defs_fields import financial_transaction_fields
from .defs_fields import match_rules


@pytest.mark.parametrize(
    "left, right, match_map, ignore_left, ignore_right, ignore_undef, expected",
    [
        (  # 0
            {"A": 0, "B": 1, "C": None},  # left
            {"A": 0, "B": 1, "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            None,  # ignore_undef
            True,
        ),
        (  # 1: mismatch in B/b
            {"A": 0, "B": 1, "C": None},  # left
            {"A": 0, "b": 1, "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            None,  # ignore_undef
            False,
        ),
        (  # 2
            {"A": 0, "B": 1, "C": None},  # left
            {"a": 0, "B": 1, "C": None},  # right
            {"a": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            None,  # ignore_undef
            True,
        ),
        (  # 3: mismatch in B/b
            {"A": 0, "B": 1, "C": None},  # left
            {"A": 0, "b": 1, "C": None},  # right
            {"A": "A"},  # match_map
            ["B"],  # ignore_left
            ["b"],  # ignore_right
            None,  # ignore_undef
            True,
        ),
        (  # 4: mismatch in B/b
            {"A": 0, "B": 1, "C": None},  # left
            {"A": 0, "b": 1, "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            [None],  # ignore_undef
            True,
        ),
        (  # 5: ignore non-None on right
            {"A": 0, "B": "hallo", "C": None},  # left
            {"A": 0, "B": "", "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            [""],  # ignore_undef
            True,
        ),
        (  # 6: ignore non-None on left
            {"A": 0, "B": "", "C": None},  # left
            {"A": 0, "B": "hallo", "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            [""],  # ignore_undef
            True,
        ),
        (  # 7: ignore works with Decimal
            {"A": 0, "B": Decimal("1.0"), "C": None},  # left
            {"A": 0, "B": "", "C": None},  # right
            {"A": "A"},  # match_map
            None,  # ignore_left
            None,  # ignore_right
            [None, ""],  # ignore_undef
            True,
        ),
    ],
)
def test_dicts_match_by_map_yields(
    left: dict[str, int | None] | dict[str, int | str | None] | dict[str, int | Decimal | None],
    right: dict[str, int | None] | dict[str, int | str | None],
    match_map: dict[str, str],
    ignore_left: None | list[str],
    ignore_right: None | list[str],
    ignore_undef: None | list[None] | list[str] | list[str | None],
    expected: bool,
):
    assert dicts_match_by_map(left, right, match_map, ignore_left, ignore_right, ignore_undef) is expected


def test_pick_one():
    left = [
        {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5},
        {"A": 2, "B": 3, "C": 4, "D": 5, "E": 5},
        {"A": 3, "B": 4, "C": 5, "D": 6, "E": 5},
        {"A": 4, "B": 5, "C": 6, "D": 7, "E": 5},
        {"A": 5, "B": 6, "C": 7, "D": 8, "E": 5},
        {"A": 6, "B": 7, "C": 8, "D": 9, "E": 5},
    ]

    result = pick_one(
        left,
        right={"A": 3, "B": 4, "c": 5, "d": 6, "e": 5},
        match_map={"c": "C", "d": "D"},
        ignore_values=[None],
        remove_match=True,
    )
    assert len(left) == 5
    assert result["A"] == 3


def test_importable_merge_two_swap_with_fee():
    """This test reuses data from test_add_to_importable_using_import_spec_with_implicit_1()"""
    data_vector = [
        {
            "imported_from": "sub0-sub1:test:1",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "asset_amount": Decimal("41.00000000"),
            "asset_currency": "ASSET5",
        },
        {
            "imported_from": "sub0-sub1:test:2",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-16.09250000"),
            "quote_currency": "ASSET4",
        },
        {
            "imported_from": "sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "fee_amount": Decimal("-0.04100000"),
            "fee_currency": "ASSET5",
        },
    ]

    tgt = ImporTable(financial_transaction_fields)
    for data in data_vector:
        src = ImporTable(financial_transaction_fields)
        src.data_vector.append(data)
        tgt = importable_merge_two(src, tgt, match_rules, addable_fields)

    assert tgt.data_vector == [
        {
            "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2|sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "asset_amount": Decimal("41.00000000"),
            "asset_currency": "ASSET5",
            "quote_amount": Decimal("-16.09250000"),
            "quote_currency": "ASSET4",
            "fee_amount": Decimal("-0.04100000"),
            "fee_currency": "ASSET5",
        },
    ]


def test_importable_merge_one_swap_with_fee():
    """This test reuses data from test_add_to_importable_using_import_spec_with_implicit_2()"""
    data_vector = [
        {
            "imported_from": "sub0-sub1:test:1",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "asset_amount": Decimal("41.00000000"),
            "asset_currency": "ASSET5",
        },
        {
            "imported_from": "sub0-sub1:test:2",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-16.09250000"),
            "quote_currency": "ASSET4",
        },
        {
            "imported_from": "sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "fee_amount": Decimal("-0.04100000"),
            "fee_currency": "ASSET5",
        },
    ]

    tgt = ImporTable(financial_transaction_fields)
    for data in data_vector:
        tgt = importable_merge_one(tgt, data, match_rules, addable_fields)

    assert tgt.data_vector == [
        {
            "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2|sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 21:13:39",
            "tx_datetime": datetime.datetime(2023, 1, 17, 21, 13, 39),
            "tx_type": "SWAP",
            "asset_amount": Decimal("41.00000000"),
            "asset_currency": "ASSET5",
            "quote_amount": Decimal("-16.09250000"),
            "quote_currency": "ASSET4",
            "fee_amount": Decimal("-0.04100000"),
            "fee_currency": "ASSET5",
        },
    ]


def test_importable_merge_one_two_swaps_no_fee():
    """This test reuses data from test_add_to_importable_using_import_spec_with_implicit_3()"""
    data_vector = [
        {
            "imported_from": "sub0-sub1:test:1",
            "tx_reference": "sub0-554122933-Sub1-2023-01-23 15:33:20",
            "tx_datetime": datetime.datetime(2023, 1, 23, 15, 33, 20),
            "tx_type": "SWAP",
            "asset_amount": Decimal("24.90000000"),
            "asset_currency": "ASSET3",
        },
        {
            "imported_from": "sub0-sub1:test:2",
            "tx_reference": "sub0-554122933-Sub1-2023-01-23 15:33:20",
            "tx_datetime": datetime.datetime(2023, 1, 23, 15, 33, 20),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-43.27620000"),
            "quote_currency": "ASSET1",
        },
        {
            "imported_from": "sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-25 00:01:28",
            "tx_datetime": datetime.datetime(2023, 1, 25, 0, 1, 28),
            "tx_type": "SWAP",
            "quote_amount": Decimal("41.90670000"),
            "quote_currency": "ASSET1",
        },
        {
            "imported_from": "sub0-sub1:test:4",
            "tx_reference": "sub0-554122933-Sub1-2023-01-25 00:01:28",
            "tx_datetime": datetime.datetime(2023, 1, 25, 0, 1, 28),
            "tx_type": "SWAP",
            "asset_amount": Decimal("-24.90000000"),
            "asset_currency": "ASSET3",
        },
    ]

    tgt = ImporTable(financial_transaction_fields)
    for data in data_vector:
        tgt = importable_merge_one(tgt, data, match_rules, addable_fields)

    assert tgt.data_vector == [
        {
            "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2",
            "tx_reference": "sub0-554122933-Sub1-2023-01-23 15:33:20",
            "tx_datetime": datetime.datetime(2023, 1, 23, 15, 33, 20),
            "tx_type": "SWAP",
            "asset_amount": Decimal("24.90000000"),
            "asset_currency": "ASSET3",
            "quote_amount": Decimal("-43.27620000"),
            "quote_currency": "ASSET1",
        },
        {
            "imported_from": "sub0-sub1:test:3|sub0-sub1:test:4",
            "tx_reference": "sub0-554122933-Sub1-2023-01-25 00:01:28",
            "tx_datetime": datetime.datetime(2023, 1, 25, 0, 1, 28),
            "tx_type": "SWAP",
            "asset_amount": Decimal("-24.90000000"),
            "asset_currency": "ASSET3",
            "quote_amount": Decimal("41.90670000"),
            "quote_currency": "ASSET1",
        },
    ]


def test_importable_merge_one_swap_with_fee_and_refund():
    data_vector = [
        {
            "imported_from": "sub0-sub1:test:1",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2023, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "quote_amount": Decimal("-15.37900000"),
            "quote_currency": "ASSET4",
        },
        {
            "imported_from": "sub0-sub1:test:2",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2023, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "asset_amount": Decimal("0.91000000"),
            "asset_currency": "ASSET0",
        },
        {
            "imported_from": "sub0-sub1:test:3",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2023, 1, 17, 2, 2, 32),
            "refund_amount": Decimal("0.00009100"),
            "refund_currency": "ASSET0",
        },
        {
            "imported_from": "sub0-sub1:test:4",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2023, 1, 17, 2, 2, 32),
            "fee_amount": Decimal("-0.00091000"),
            "fee_currency": "ASSET0",
        },
    ]

    tgt = ImporTable(financial_transaction_fields)
    for data in data_vector:
        tgt = importable_merge_one(tgt, data, match_rules, addable_fields)

    assert tgt.data_vector == [
        {
            "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2|sub0-sub1:test:3|sub0-sub1:test:4",
            "tx_reference": "sub0-554122933-Sub1-2023-01-17 02:02:32",
            "tx_datetime": datetime.datetime(2023, 1, 17, 2, 2, 32),
            "tx_type": "SWAP",
            "asset_amount": Decimal("0.91000000"),
            "asset_currency": "ASSET0",
            "quote_amount": Decimal("-15.37900000"),
            "quote_currency": "ASSET4",
            "fee_amount": Decimal("-0.00091000"),
            "fee_currency": "ASSET0",
            "refund_amount": Decimal("0.00009100"),
            "refund_currency": "ASSET0",
        }
    ]


def test_importable_merge_can_add_subtrades():
    """This test can only work if two positions of same currency can be added during the merge."""

    # 554122933,2023-01-18 16:00:24,Sub1,Sell,ASSET2,-0.50000000,""
    # 554122933,2023-01-18 16:00:24,Sub1,Sell,ASSET1,23.71764800,""
    # 554122933,2023-01-18 16:00:24,Sub1,Sell,ASSET1,0.00145400,""
    # 554122933,2023-01-18 16:00:24,Sub1,Sell,ASSET2,-8156.00000000,""

    # pairs of incremental input data and merged result
    data_vector: list[tuple[dict, dict]] = [
        (
            {
                "imported_from": "sub0-sub1:test:1",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-0.50000000"),
                "asset_currency": "ASSET2",
                "_allow_add": True,
            },
            {
                "imported_from": "sub0-sub1:test:1",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-0.50000000"),
                "asset_currency": "ASSET2",
                "_allow_add": True,
            },
        ),
        (
            {
                "imported_from": "sub0-sub1:test:2",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "quote_amount": Decimal("23.71764800"),
                "quote_currency": "ASSET1",
                "_allow_add": True,
            },
            {
                "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-0.50000000"),
                "asset_currency": "ASSET2",
                "quote_amount": Decimal("23.71764800"),
                "quote_currency": "ASSET1",
                "_allow_add": True,
            },
        ),
        (
            {
                "imported_from": "sub0-sub1:test:3",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "quote_amount": Decimal("0.00145400"),
                "quote_currency": "ASSET1",
                "_allow_add": True,
            },
            {
                "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-0.50000000"),
                "asset_currency": "ASSET2",
                "quote_amount": Decimal("23.71764800") + Decimal("0.00145400"),
                "quote_currency": "ASSET1",
                "_allow_add": True,
            },
        ),
        (
            {
                "imported_from": "sub0-sub1:test:4",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-8156.00000000"),
                "asset_currency": "ASSET2",
                "_allow_add": True,
            },
            {
                "imported_from": "sub0-sub1:test:1|sub0-sub1:test:2",
                "tx_reference": "sub0-554122933-Sub1-2023-01-18 16:00:24",
                "tx_datetime": datetime.datetime(2023, 1, 18, 16, 0, 24),
                "tx_type": "SWAP",
                "asset_amount": Decimal("-0.50000000") + Decimal("-8156.00000000"),
                "asset_currency": "ASSET2",
                "quote_amount": Decimal("23.71764800") + Decimal("0.00145400"),
                "quote_currency": "ASSET1",
                "_allow_add": True,
            },
        ),
    ]

    tgt = ImporTable(financial_transaction_fields)
    for idx, (input, output) in enumerate(data_vector):
        tgt = importable_merge_one(tgt, input, match_rules, addable_fields)
        # will fail unless _allow_add is properly implemented!
        assert tgt.data_vector == [output], f"Mismatch after merge step {idx}"
