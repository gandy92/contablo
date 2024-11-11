import pytest
from pydantic import ValidationError

from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportMatchRule
from contablo.importspec import ImportSpec


def test_import_match_rule_noargs():
    with pytest.raises(ValidationError):
        ImportMatchRule()


def test_import_match_rule_minimal():
    obj = ImportMatchRule(rule="testme")
    assert obj.rule == "testme"
    assert obj.implies == dict()
    assert obj.onlyif == dict()


def test_import_column_spec_noargs():
    with pytest.raises(ValidationError):
        ImportColumnSpec()


def test_import_column_spec_minimal():
    obj = ImportColumnSpec(label="Verwendungszweck", field="note")
    assert obj.label == "Verwendungszweck"
    assert obj.field == "note"
    assert obj.match == []
    assert obj.samples == []


def test_import_column_spec():
    obj = ImportColumnSpec(
        label="Verwendungszweck",
        field="note",
        match=[
            ImportMatchRule(rule="Kauf WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}$", implies={"type": "BUY"}),
            ImportMatchRule(
                rule="WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}",
                implies={"type": "DIVIDEND", "fees": "0,00"},
                onlyif={"value+fees": "positive"},
            ),
        ],
    )
    assert obj.samples == []


# def test_import_spec_matches():
#     # Todo: implement test for ImportSpec.matches - might be a big one


def test_import_spec_realistic():
    obj = ImportSpec(
        label="acct2-Konto",
        type="account",
        defaults={"asset_type": "stock", "quote_currency": "EUR"},
        columns=[
            ImportColumnSpec(label="Datum", field="date"),
            ImportColumnSpec(label="Betrag", field="value+fees", format="-0.000,00"),
            ImportColumnSpec(
                label="Verwendungszweck",
                field="note",
                match=[
                    ImportMatchRule(rule="Kauf WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}$", implies={"type": "BUY"}),
                    ImportMatchRule(
                        rule="WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}",
                        implies={"type": "DIVIDEND", "fees": "0,00"},
                        onlyif={"value+fees": "positive"},
                    ),
                    ImportMatchRule(rule="bekannt", implies={"type": "DEPOSIT"}),
                ],
                samples=[
                    "Kauf WP-Kenn-Nr.: 502391, Ford Motor Co., Nominale:  110,0000",
                    "WP-Kenn-Nr.: 858144, Union Pacific Corp., Nominale:  1,0000",
                    "bekannt",
                ],
            ),
            ImportColumnSpec(
                label="Referenznummer",
                field="reference",
                samples=[],
            ),
        ],
    )
    assert obj is not None
    assert isinstance(obj.label, str)
    assert isinstance(obj.type, str)
    assert obj.encoding is None
    assert isinstance(obj.skip_lines, int)
    assert isinstance(obj.delimiter, str)
    assert isinstance(obj.defaults, dict)
    assert isinstance(obj.columns, list)


def test_import_spec_forbid_extra():
    with pytest.raises(ValidationError):
        ImportSpec(label="acct2-Konto", type="account", something="else")
