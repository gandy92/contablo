import datetime
from decimal import Decimal

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
    "cls, kwargs",  # provide args required to succesfully create a class instance
    [
        (BoolFieldSpec, dict(name="test", help="")),
        (DateFieldSpec, dict(name="test", help="")),
        (DateTimeFieldSpec, dict(name="test", help="")),
        (DecimalFieldSpec, dict(name="test", help="")),
        (EnumFieldSpec, dict(name="test", help="", items=["one", "two"])),
        (IntFieldSpec, dict(name="test", help="")),
        (StringFieldSpec, dict(name="test", help="")),
        (TimeFieldSpec, dict(name="test", help="")),
    ],
)
def test_builtin_field_spec_rejects_overrides(cls, kwargs):
    for protected in ["type", "zero"]:
        kwargs[protected] = "wrong"
        try:
            cls(**kwargs)
        except TypeError as e:
            if "unexpected keyword argument" not in str(e):
                raise
        else:
            raise AssertionError(f"{cls}.__init__() should reject argument {protected}.")


@pytest.mark.parametrize(
    "value, format, expected",
    [
        ("+1.234,55", "+1.000,00", Decimal("1234.55")),
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
        ("05. Februar 2024", "%d %B %Y", datetime.date(2024, 2, 5)),
        ("07. August 2024", "%d %B %Y", datetime.date(2024, 8, 7)),
        ("07. Mai 2024", "%d %B %Y", datetime.date(2024, 5, 7)),
        ("07. May 2024", "%d %B %Y", datetime.date(2024, 5, 7)),
        ("09. August 2024", "%d %B %Y", datetime.date(2024, 8, 9)),
        ("10. Juli 2024", "%d %B %Y", datetime.date(2024, 7, 10)),
        ("10 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 10)),
        ("11 Jun 2024", "%d %B %Y", datetime.date(2024, 6, 11)),
        ("11 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 11)),
        ("12 Mrz 2024", "%d %B %Y", datetime.date(2024, 3, 12)),
        ("16 Aug 2024", "%d %B %Y", datetime.date(2024, 8, 16)),
        ("16 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 16)),
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
        ("1 Okt 2024 13:05:20", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 10, 1, 13, 5, 20)),
        ("14 Aug 2024 10:22:41", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 8, 14, 10, 22, 41)),
        ("14 Jun 2024 10:28:55", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 6, 14, 10, 28, 55)),
        ("14 Jun 2024 10:29:44", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 6, 14, 10, 29, 44)),
        ("2 Nov 2023 15:42:24", "%d %B %Y %H:%M:%S", datetime.datetime(2023, 11, 2, 15, 42, 24)),
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
