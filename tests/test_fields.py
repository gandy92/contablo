import datetime
from decimal import Decimal as RP2Decimal

import pytest

from contablo.fields import BoolFieldSpec
from contablo.fields import DateFieldSpec
from contablo.fields import DateTimeFieldSpec
from contablo.fields import DecimalFieldSpec
from contablo.fields import EnumFieldSpec
from contablo.fields import FieldSpecRegistry
from contablo.fields import IntFieldSpec
from contablo.fields import StringFieldSpec
from contablo.fields import TimeFieldSpec
from contablo.fields import add_builtin_fieldspecs_to_registry


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("10", "", 10),
        ("010", "", 10),
    ],
)
def test_int_field_spec_convert_yields(value, format, expected):
    assert IntFieldSpec.convert(value, format) == expected


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("+1.234,55", "+1.000,00", RP2Decimal("1234.55")),
    ],
)
def test_decimal_field_spec_convert_yields(value, format, expected):
    assert DecimalFieldSpec.convert(value, format) == expected


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("13.11.23", "%d.%m.%y", datetime.date(2023, 11, 13)),
        ("13.11.2023", "%d.%m.%Y", datetime.date(2023, 11, 13)),
        ("11/13/23", "%m/%d/%y", datetime.date(2023, 11, 13)),
        ("2023-11-13", "", datetime.date(2023, 11, 13)),
        ("1714938611", "", datetime.date(2024, 5, 5)),
        ("1714938611.0", "", datetime.date(2024, 5, 5)),
    ],
)
def test_date_field_spec_convert_yields(value, format, expected):
    assert DateFieldSpec.convert(value, format) == expected


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("01:02:03", "%H:%M:%S", datetime.time(1, 2, 3)),
        ("010203", "%H%M%S", datetime.time(1, 2, 3)),
    ],
)
def test_time_field_spec_convert_yields(value, format, expected):
    assert TimeFieldSpec.convert(value, format) == expected


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("1714938611", "", datetime.datetime(2024, 5, 5, 21, 50, 11)),
        ("1714938611.0", "", datetime.datetime(2024, 5, 5, 21, 50, 11)),
        ("1714938611000.0", "", datetime.datetime(2024, 5, 5, 21, 50, 11)),
        ("1714938611000000.0", "", datetime.datetime(2024, 5, 5, 21, 50, 11)),
        ("1714938611000000000.0", "", datetime.datetime(2024, 5, 5, 21, 50, 11)),
        # Todo: Add more tests with TZ format and custom strptime formats
    ],
)
def test_datetime_field_spec_convert_yields(value, format, expected):
    assert DateTimeFieldSpec.convert(value, format) == expected


def test_field_spec_registry():
    fsr = FieldSpecRegistry()

    fsr.add(BoolFieldSpec)
    fsr.add(DateFieldSpec)
    fsr.add(DateTimeFieldSpec)
    fsr.add(DecimalFieldSpec)
    fsr.add(EnumFieldSpec)
    fsr.add(IntFieldSpec)
    fsr.add(StringFieldSpec)
    fsr.add(TimeFieldSpec)


def test_field_spec_registry_make_spec_list():
    fsr = FieldSpecRegistry()
    fsr.add(DateFieldSpec)

    specs = fsr.make_spec_list([{"name": "Datum", "type": "date", "help": "The date"}])

    assert specs[0] == DateFieldSpec(name="Datum", help="The date")


def test_add_builtin_fieldspecs_to_registry():
    fsr = FieldSpecRegistry()
    add_builtin_fieldspecs_to_registry(fsr)

    specs = fsr.make_spec_list(
        [
            {"name": "tx_date", "type": "date", "help": "Date of payment"},
            {"name": "payee", "type": "string", "help": "Person or institution sending or receiving the payment"},
            {"name": "note", "type": "string", "help": "Transaction notes"},
            {"name": "iban", "type": "string", "help": "Payee IBAN"},
            {"name": "bic", "type": "string", "help": "Payee BIC, if applicable"},
            {"name": "amount", "type": "number", "help": "Payment amount"},
            {"name": "balance", "type": "number", "help": "New account balance"},
        ]
    )

    assert specs[0] == DateFieldSpec(name="tx_date", help="Date of payment")
