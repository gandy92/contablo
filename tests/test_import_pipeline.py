"""Characterization tests for the CSV import pipeline.

These tests pin the current end-to-end behavior of reading CSV files with import specs: rows dropped via implies,
map/ignore, columns expected to be empty, match rules with onlyif and column placeholders, defaults with templates
and formats, extra fields with transforms, spec detection and spec matching. All names and values are arbitrary.
"""

import datetime
from decimal import Decimal
from pathlib import Path

import pytest
from arithmetic_expressions.engine import UndefinedVariableError

from contablo.csv_helper import ChunkInfo
from contablo.csv_helper import CsvFileInfo
from contablo.csvimporter import ImportColumnMismatchError
from contablo.csvimporter import import_csv_with_spec
from contablo.csvimporter import import_csv_with_spec_detection
from contablo.fields import FieldSpecRegistry
from contablo.fields import add_builtin_fieldspecs_to_registry
from contablo.importable import ImporTable
from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportMatchRule
from contablo.importspec import ImportSpec
from contablo.importspec import ImportSpecRegistry

from .defs_fields import financial_transaction_fields


@pytest.fixture
def field_registry() -> FieldSpecRegistry:
    registry = FieldSpecRegistry()
    add_builtin_fieldspecs_to_registry(registry)
    return registry


@pytest.fixture
def factory():
    return ImporTable(financial_transaction_fields).clone_empty


def write_csv(path: Path, lines: list[str], encoding: str = "utf-8") -> str:
    path.write_text("\n".join(lines) + "\n", encoding=encoding)
    return path.as_posix()


# --- spec A: drop via implies, plain defaults ------------------------------------------------------------------

spec_a = ImportSpec(
    label="spec-a",
    type="account",
    encoding="us-ascii",
    delimiter=";",
    defaults={"quote_currency": "CUR1"},
    columns=[
        ImportColumnSpec(label="A1", field="tx_date", format="dd.mm.yyyy"),
        ImportColumnSpec(label="A2", field="quote_amount", format="1.000,00"),
        ImportColumnSpec(
            label="A3",
            field="note",
            match=[
                ImportMatchRule(rule="kw-alpha", implies={"tx_type": "DEPOSIT"}),
                ImportMatchRule(rule="kw-beta{}", implies={"drop": "drop"}),
            ],
        ),
        ImportColumnSpec(label="A4", field="reference"),
    ],
)
spec_a_header = "A1;A2;A3;A4"


def test_import_drops_rows_implying_drop(tmp_path, factory, field_registry):
    csv_file = write_csv(
        tmp_path / "a.csv",
        [spec_a_header, "01.11.2021;1.234,50;kw-alpha;ref-1", "02.11.2021;5,00;kw-beta 123;ref-2"],
    )
    result = import_csv_with_spec(csv_file, spec_a, factory, field_registry)
    assert result.data_vector == [
        {
            "imported_from": "spec-a:a.csv:2",
            "quote_currency": "CUR1",
            "tx_date": datetime.date(2021, 11, 1),
            "quote_amount": Decimal("1234.50"),
            "note": "kw-alpha",
            "reference": "ref-1",
            "tx_type": "DEPOSIT",
        }
    ]


def test_import_raises_on_column_mismatch(tmp_path, factory, field_registry):
    csv_file = write_csv(tmp_path / "other.csv", ["X1;X2;X3;X4", "1;2;3;4"])
    with pytest.raises(ImportColumnMismatchError):
        import_csv_with_spec(csv_file, spec_a, factory, field_registry)


def test_import_does_not_skip_leading_metadata_chunk(tmp_path, factory, field_registry):
    """Current behavior: a mismatching first chunk aborts the import instead of trying the next chunk."""
    csv_file = write_csv(
        tmp_path / "meta.csv",
        ["K1;V1", "", spec_a_header, "01.11.2021;1,00;kw-alpha;ref-1"],
    )
    with pytest.raises(ImportColumnMismatchError):
        import_csv_with_spec(csv_file, spec_a, factory, field_registry)


def test_import_of_empty_file_fails_on_encoding_detection(tmp_path, factory, field_registry):
    """Current behavior: libmagic reports an empty file as 'binary', which is no valid codec."""
    csv_file = write_csv(tmp_path / "empty.csv", [""])
    with pytest.raises(LookupError):
        import_csv_with_spec(csv_file, spec_a, factory, field_registry)


# --- spec B: map, ignore, field "empty", defaults with format --------------------------------------------------

spec_b = ImportSpec(
    label="spec-b",
    type="depot",
    delimiter=";",
    defaults={"quote_currency": "CUR1", "tx_time": "12:00:00/HH:MM:SS"},
    columns=[
        ImportColumnSpec(label="B1", field="tx_date", format="dd.mm.yyyy"),
        ImportColumnSpec(label="B2", field="tx_type", map={"val-x": "BUY", "val-y": "BUY"}),
        ImportColumnSpec(label="B3", field="empty"),
        ImportColumnSpec(label="B4", field="asset_amount", format="1.000,00", ignore=["0"]),
        ImportColumnSpec(
            label="B5",
            field="tax_amount",
            format="1000,00",
            ignore=["0"],
            match=[ImportMatchRule(rule="{}", implies={"tax_currency": "CUR1"})],
        ),
    ],
)
spec_b_header = "B1;B2;B3;B4;B5"


def test_import_map_ignore_empty_and_formatted_defaults(tmp_path, factory, field_registry):
    csv_file = write_csv(
        tmp_path / "b.csv",
        [spec_b_header, "03.01.2022;val-x;;1.000,123;0", "04.01.2022;val-y;;0;1,50"],
    )
    result = import_csv_with_spec(csv_file, spec_b, factory, field_registry)
    assert result.data_vector == [
        {
            "imported_from": "spec-b:b.csv:2",
            "quote_currency": "CUR1",
            "tx_time": datetime.time(12, 0),
            "tx_date": datetime.date(2022, 1, 3),
            "tx_type": "BUY",
            "asset_amount": Decimal("1000.123"),
        },
        {
            "imported_from": "spec-b:b.csv:3",
            "quote_currency": "CUR1",
            "tx_time": datetime.time(12, 0),
            "tx_date": datetime.date(2022, 1, 4),
            "tx_type": "BUY",
            "tax_amount": Decimal("1.50"),
            "tax_currency": "CUR1",
        },
    ]


def test_import_empty_field_with_value_is_reported_and_dropped(tmp_path, factory, field_registry, capsys):
    csv_file = write_csv(tmp_path / "b.csv", [spec_b_header, "03.01.2022;val-x;x;1,0;0"])
    result = import_csv_with_spec(csv_file, spec_b, factory, field_registry)
    assert "Expecting <B3> to be empty, but got <x>" in capsys.readouterr().out
    assert len(result) == 1
    assert "x" not in result.data_vector[0].values()


# --- spec C: onlyif with column placeholders, templated defaults -----------------------------------------------

spec_c = ImportSpec(
    label="spec-c",
    type="depot",
    defaults={"tx_reference": "c-{C1}-{C2}"},
    columns=[
        ImportColumnSpec(label="C1"),
        ImportColumnSpec(label="C2", field="tx_datetime", format="yyyy-mm-dd HH:MM:SS"),
        ImportColumnSpec(
            label="C3",
            match=[
                ImportMatchRule(
                    rule="op-1",
                    implies={"tx_type": "SWAP", "asset_amount": "{C5}/1000.00", "asset_currency": "{C4}"},
                    onlyif={"C5": ">:0.00:number:1000.00"},
                ),
                ImportMatchRule(
                    rule="op-1",
                    implies={"tx_type": "SWAP", "quote_amount": "{C5}/1000.00", "quote_currency": "{C4}"},
                    onlyif={"C5": "<:0.00:number:1000.00"},
                ),
                ImportMatchRule(rule="op-2", implies={"fee_amount": "{C5}/1000.00", "fee_currency": "{C4}"}),
            ],
        ),
        ImportColumnSpec(label="C4"),
        ImportColumnSpec(label="C5"),
    ],
)


def test_import_onlyif_and_placeholders(tmp_path, factory, field_registry):
    csv_file = write_csv(
        tmp_path / "c.csv",
        [
            "C1,C2,C3,C4,C5",
            "42,2023-01-18 16:00:24,op-1,CUR2,0.5",
            "42,2023-01-18 16:00:24,op-1,CUR1,-8156.00",
            "42,2023-01-18 16:00:24,op-2,CUR3,-0.001",
        ],
    )
    result = import_csv_with_spec(csv_file, spec_c, factory, field_registry)
    ts = datetime.datetime(2023, 1, 18, 16, 0, 24)
    ref = "c-42-2023-01-18 16:00:24"
    assert result.data_vector == [
        {
            "imported_from": "spec-c:c.csv:2",
            "tx_reference": ref,
            "tx_datetime": ts,
            "tx_type": "SWAP",
            "asset_amount": Decimal("0.5"),
            "asset_currency": "CUR2",
        },
        {
            "imported_from": "spec-c:c.csv:3",
            "tx_reference": ref,
            "tx_datetime": ts,
            "tx_type": "SWAP",
            "quote_amount": Decimal("-8156.00"),
            "quote_currency": "CUR1",
        },
        {
            "imported_from": "spec-c:c.csv:4",
            "tx_reference": ref,
            "tx_datetime": ts,
            "fee_amount": Decimal("-0.001"),
            "fee_currency": "CUR3",
        },
    ]


# --- extra fields and transforms -------------------------------------------------------------------------------


def transform_spec(label: str, extra: list[str], transform: str) -> ImportSpec:
    return ImportSpec(
        label=label,
        type="account",
        delimiter=";",
        defaults={"tx_type": "DIVIDEND"},
        fields=[{"name": name, "type": "number", "help": name} for name in extra],
        transforms={"tax_amount": transform},
        columns=[ImportColumnSpec(label="D1", field="quote_amount", format="1000,00")]
        + [ImportColumnSpec(label=name, field=name, format="1000,00") for name in extra],
    )


def test_import_extra_fields_and_transforms(tmp_path, factory, field_registry):
    spec = transform_spec("spec-d", ["x1", "x2"], "x1 + x2")
    csv_file = write_csv(tmp_path / "d.csv", ["D1;x1;x2", "10,00;2,50;0,13", "5,00;1,00;"])
    result = import_csv_with_spec(csv_file, spec, factory, field_registry)
    assert [row["tax_amount"] for row in result.data_vector] == [Decimal("2.63"), Decimal("1.00")]
    assert result.export_columns == [f.name for f in financial_transaction_fields]
    assert "x1" in result.columns and "x1" not in result.export_columns


def test_import_transform_context_does_not_leak_between_importables(tmp_path, factory, field_registry):
    first = transform_spec("spec-d1", ["x1", "x2"], "x1 + x2")
    second = transform_spec("spec-d2", ["x1"], "x1 + x2")
    csv_1 = write_csv(tmp_path / "d1.csv", ["D1;x1;x2", "10,00;2,50;0,13"])
    csv_2 = write_csv(tmp_path / "d2.csv", ["D1;x1", "10,00;2,50"])
    import_csv_with_spec(csv_1, first, factory, field_registry)
    with pytest.raises(UndefinedVariableError):
        import_csv_with_spec(csv_2, second, factory, field_registry)


# --- spec detection --------------------------------------------------------------------------------------------


def make_registry(*specs: ImportSpec) -> ImportSpecRegistry:
    registry = ImportSpecRegistry()
    for spec in specs:
        registry.add_import_spec(spec, f"{spec.label}.json")
    return registry


def test_detection_picks_the_single_matching_spec(tmp_path, factory, field_registry):
    csv_file = write_csv(tmp_path / "a.csv", [spec_a_header, "01.11.2021;1,00;kw-alpha;ref-1"])
    result = import_csv_with_spec_detection(csv_file, make_registry(spec_b, spec_a), factory, field_registry)
    assert len(result) == 1
    assert result.data_vector[0]["imported_from"] == "spec-a:a.csv:2"


def test_detection_returns_none_without_match(tmp_path, factory, field_registry, capsys):
    csv_file = write_csv(tmp_path / "x.csv", ["X1;X2", "1;2"])
    assert import_csv_with_spec_detection(csv_file, make_registry(spec_a), factory, field_registry) is None
    assert "Found no match" in capsys.readouterr().out


def test_detection_returns_none_for_ambiguous_match(tmp_path, factory, field_registry, capsys):
    csv_file = write_csv(tmp_path / "a.csv", [spec_a_header, "01.11.2021;1,00;kw-alpha;ref-1"])
    twin = spec_a.model_copy(update={"label": "spec-a-twin"})
    assert import_csv_with_spec_detection(csv_file, make_registry(spec_a, twin), factory, field_registry) is None
    assert "More than one specs matches" in capsys.readouterr().out


def test_detection_reports_exceptions_and_continues(tmp_path, factory, field_registry, capsys):
    csv_file = write_csv(tmp_path / "a.csv", [spec_a_header, "01.11.2021;1,00;kw-unknown;ref-1"])
    assert import_csv_with_spec_detection(csv_file, make_registry(spec_a), factory, field_registry) is None
    out = capsys.readouterr().out
    assert "Exception trying spec-a" in out
    assert "Found no match" in out


# --- ImportSpec.matches / registry queries ---------------------------------------------------------------------


def file_info(encoding="us-ascii", first_line=1, delimiter=";", columns=None) -> CsvFileInfo:
    columns = columns if columns is not None else spec_a.column_labels
    return CsvFileInfo(
        source_files=["f.csv"],
        file_encoding=encoding,
        chunk_info=[ChunkInfo(delimiter=delimiter, first_line=first_line, columns=columns, datalines=[])],
    )


@pytest.mark.parametrize(
    "info, expected",
    [
        (file_info(), True),
        (file_info(encoding="utf-8"), False),
        (file_info(first_line=2), False),
        (file_info(delimiter=","), False),
        (file_info(columns=["A1"]), False),
    ],
)
def test_import_spec_matches(info, expected):
    assert spec_a.matches(info) is expected


def test_import_spec_matches_any_chunk():
    info = file_info()
    info.chunk_info.insert(0, ChunkInfo(delimiter=";", first_line=1, columns=["", ""], datalines=[]))
    assert spec_a.matches(info) is True


def test_import_spec_matches_rejects_other_types():
    assert spec_a.matches("not a file info") is False


def test_registry_queries():
    registry = make_registry(spec_b, spec_a)
    assert list(registry.iter_specs()) == [spec_b, spec_a]
    assert registry.query_by_file_info(file_info()) is spec_a
    assert registry.query_by_file_info(file_info(encoding="utf-8")) is None
    assert registry.query_source("spec-a") == "spec-a.json"
    assert registry.query_source("unknown") is None
