import datetime
import json
from decimal import Decimal

from contablo.csvimporter import import_csv_with_spec
from contablo.fields import FieldSpecRegistry
from contablo.fields import add_builtin_fieldspecs_to_registry
from contablo.importable import ImporTable
from contablo.importspec import ImportSpec

import_spec = {
    "label": "export-dividends",
    "type": "account",
    "encoding": "utf-8-sig",
    "skip_lines": 0,
    "fields": [
        {"name": "dividend_tax", "type": "number", "help": "Redacted diviend tax"},
        {"name": "solidary_tax", "type": "number", "help": "Redacted solidary tax"},
        {"name": "church_tax", "type": "number", "help": "Redacted church tax"},
        {"name": "tax_at_source", "type": "number", "help": "Redacted tax at source"},
    ],
    "transforms": {"tax_amount": "tax_at_source + dividend_tax + solidary_tax + church_tax"},
    "defaults": {"tx_type": "DIVIDEND"},
    "columns": [
        {"label": "ISIN", "field": "isin"},
        {"label": "Valutatag", "field": "tx_date", "format": "dd mmm yyyy"},
        {"label": "Dividendengutschrift", "field": "", "format": "1000,00"},
        {"label": "Einbehaltende Quellensteuer", "field": "tax_at_source", "format": "1000,00"},
        {"label": "Anrechenbare Quellensteuer", "field": "", "format": "1000,00"},
        {"label": "Verrechnete Quellensteuer", "field": "", "format": "1000,00"},
        {"label": "Berechnungsgrundlage", "field": "", "format": "1000,00"},
        {"label": "Kapitalertragssteuer", "field": "dividend_tax", "format": "1000,00"},
        {"label": "Solidaritätszuschlag", "field": "solidary_tax", "format": "1000,00"},
        {"label": "Kirchensteuer", "field": "church_tax", "format": "1000,00"},
        {"label": "Bruttoertrag", "field": "", "format": "1000,00"},
        {"label": "Betrag", "field": "amount", "format": "1000,00"},
    ],
}

target_field_specs = [
    {"name": "isin", "type": "string", "help": "Asset ISIN"},
    {"name": "tx_date", "type": "date", "help": "Date of payment"},
    {"name": "tx_type", "type": "string", "help": "Type of transaction"},
    {"name": "note", "type": "string", "help": "Transaction notes"},
    {"name": "bic", "type": "string", "help": "Payee BIC, if applicable"},
    {"name": "amount", "type": "number", "help": "Payment amount"},
    {"name": "tax_amount", "type": "number", "help": "Redacted taxes"},
    {"name": "fee_amount", "type": "number", "help": "Redacted fees"},
]


def test_custom_fields_with_transforms():
    fieldspecs = FieldSpecRegistry()
    add_builtin_fieldspecs_to_registry(fieldspecs)
    fields = fieldspecs.make_spec_list(target_field_specs)

    config = ImportSpec(**import_spec)
    imp = import_csv_with_spec("tests/example-4.csv", config, ImporTable(fields).clone_empty, fieldspecs)

    # print(imp.get_data())
    assert imp.get_data() == [
        {
            "imported_from": "export-dividends:example-4.csv:2",
            "tx_type": "DIVIDEND",
            "isin": "AB0123456789",
            "tx_date": datetime.date(1987, 6, 14),
            "tax_at_source": Decimal("0.44"),
            "dividend_tax": Decimal("0.28"),
            "solidary_tax": Decimal("0.01"),
            "church_tax": Decimal("0.02"),
            "amount": Decimal("2.15"),
            "tax_amount": Decimal("0.75"),
        },
        {
            "imported_from": "export-dividends:example-4.csv:3",
            "tx_type": "DIVIDEND",
            "isin": "CD0123456789",
            "tx_date": datetime.date(1987, 9, 1),
            "tax_at_source": Decimal("6.38"),
            "dividend_tax": Decimal("4.18"),
            "solidary_tax": Decimal("0.22"),
            "church_tax": Decimal("0.33"),
            "amount": Decimal("31.45"),
            "tax_amount": Decimal("11.11"),
        },
        {
            "imported_from": "export-dividends:example-4.csv:4",
            "tx_type": "DIVIDEND",
            "isin": "EF0123456789",
            "tx_date": datetime.date(1987, 10, 29),
            "tax_at_source": Decimal("0.18"),
            "dividend_tax": Decimal("0.12"),
            "amount": Decimal("0.90"),
            "tax_amount": Decimal("0.85"),
        },
        {
            "imported_from": "export-dividends:example-4.csv:5",
            "tx_type": "DIVIDEND",
            "isin": "AB0123456789",
            "tx_date": datetime.date(1987, 11, 7),
            "tax_at_source": Decimal("0.53"),
            "dividend_tax": Decimal("0.34"),
            "solidary_tax": Decimal("0.01"),
            "church_tax": Decimal("0.02"),
            "amount": Decimal("2.60"),
            "tax_amount": Decimal("0.90"),
        },
    ]
