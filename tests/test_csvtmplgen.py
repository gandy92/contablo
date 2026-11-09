"""Characterization tests for the import template generator."""

import json
from glob import glob

from contablo.csvtmplgen import CsvTemplateGenerator
from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportSpec
from contablo.importspec import ImportSpecRegistry

from .defs_fields import financial_transaction_fields

HEADER = "G1;G2;G3;G4"


def write(path, lines):
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path.as_posix()


def test_files_with_same_format_are_grouped(tmp_path):
    f1 = write(tmp_path / "g1.csv", [HEADER, "01.02.2023;val-1;1.234,50;r1"])
    f2 = write(tmp_path / "g2.csv", [HEADER, "02.02.2023;val-2;5,00;r2"])
    f3 = write(tmp_path / "h.csv", ["H1;H2;H3", "1;2;3"])
    gen = CsvTemplateGenerator(financial_transaction_fields)
    gen.add_files([f1, f2, f3])

    assert [fmt.source_files for fmt in gen.input_formats] == [[f1, f2], [f3]]
    assert gen.input_formats[0].chunk_info[0].datalines == ["01.02.2023;val-1;1.234,50;r1", "02.02.2023;val-2;5,00;r2"]


def test_files_matching_known_specs_are_skipped(tmp_path):
    f1 = write(tmp_path / "g1.csv", [HEADER, "01.02.2023;val-1;1.234,50;r1"])
    registry = ImportSpecRegistry()
    known = ImportSpec(
        label="spec-g",
        type="account",
        encoding="us-ascii",
        delimiter=";",
        columns=[ImportColumnSpec(label=label) for label in HEADER.split(";")],
    )
    registry.add_import_spec(known, "spec-g.json")
    gen = CsvTemplateGenerator(financial_transaction_fields, registry)
    gen.add_file(f1)

    assert gen.input_formats == []
    assert gen.input_specs == {"spec-g": [f1]}


def test_metadata_chunk_is_detected(tmp_path):
    f1 = write(tmp_path / "m.csv", ["K1;V1", "", HEADER, "01.02.2023;val-1;1.234,50;r1"])
    gen = CsvTemplateGenerator(financial_transaction_fields)
    gen.add_file(f1)

    chunks = gen.input_formats[0].chunk_info
    assert [(c.first_line, c.columns) for c in chunks] == [(1, ["", ""]), (3, HEADER.split(";"))]


def test_make_import_spec(tmp_path):
    f1 = write(tmp_path / "g1.csv", [HEADER, "01.02.2023;alpha beta;1.234,50;r1", "02.02.2023;gamma delta;-5,00;r2"])
    gen = CsvTemplateGenerator(financial_transaction_fields)
    gen.add_file(f1)
    spec = gen.make_import_spec(gen.input_formats[0], financial_transaction_fields)

    dump = spec.model_dump(exclude_unset=True)
    assert dump["encoding"] == "us-ascii"
    assert dump["skip_lines"] == 0
    assert dump["columns"][0] == {
        "label": "G1",
        "field": "tx_date|order_date|snapshot_date",
        "format": "dd.mm.yyyy",
    }
    assert dump["columns"][1]["samples"] == ["alpha beta", "gamma delta"]
    assert dump["columns"][2]["format"] == "-1.000,00"
    assert dump["columns"][2]["field"].startswith("asset_amount|")

    # Current behavior: short alphanumeric values are guessed as dates by the lax date parser.
    assert dump["columns"][3] == {"label": "G4", "field": "tx_date|order_date|snapshot_date", "format": "dd mmm yyyy"}

    no_samples = gen.make_import_spec(gen.input_formats[0], financial_transaction_fields, skip_samples=True)
    assert "samples" not in no_samples.model_dump(exclude_unset=True)["columns"][1]


def test_make_templates_writes_commented_json(tmp_path, capsys):
    f1 = write(tmp_path / "g1.csv", [HEADER, "01.02.2023;val-1;1.234,50;r1"])
    gen = CsvTemplateGenerator(financial_transaction_fields)
    gen.add_file(f1)

    gen.make_templates(output_path_base=None)
    assert "Not writing output file." in capsys.readouterr().out

    out_dir = tmp_path / "out"
    out_dir.mkdir()
    gen.make_templates(output_path_base=out_dir.as_posix())
    (written,) = glob((out_dir / "new_import_spec-*-01.json").as_posix())
    lines = open(written, encoding="utf8").read().splitlines()
    assert lines[:2] == ["// Generated with CsvTemplateGenerator from these files:", f"// - {f1}"]
    assert json.loads("\n".join(lines[2:]))["columns"][0]["label"] == "G1"
