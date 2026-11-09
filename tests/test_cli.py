import json
from glob import glob

from click.testing import CliRunner
from pytest import TempdirFactory

from contablo.cli import cli


def test_mk_schema():
    runner = CliRunner()
    base = "test-schema-"
    schema_name = "ImportSpec"
    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["mk-schema", "-o", base, schema_name])
        assert result.exit_code == 0

        with open(f"{base}{schema_name.lower()}.json") as f:
            schema = json.load(f)
        assert "$defs" in schema


def test_mk_import_template():
    runner = CliRunner()

    files = [
        "example-4.csv",
        "fieldspec-banking.json",
    ]
    file_data = {}
    for filename in files:
        with open(f"tests/{filename}") as f:
            file_data[filename] = f.readlines()

    with runner.isolated_filesystem():
        for filename in files:
            with open(f"{filename}", "w") as f:
                f.writelines(file_data[filename])

        result = runner.invoke(
            cli, ["mk-import-tmpl", "-t", "fieldspec-banking.json", "-o", "test_template", "example-4.csv"]
        )
        assert result.exit_code == 0
        print(result.output)

        out_files = glob("test_template*.json")
        print(out_files)
        assert len(out_files) == 1


CONVERT_SPEC = {
    "label": "spec-e",
    "type": "account",
    "encoding": "us-ascii",
    "delimiter": ";",
    "columns": [
        {"label": "E1", "field": "date", "format": "dd.mm.yyyy"},
        {"label": "E2", "field": "payee"},
        {"label": "E3", "field": "amount", "format": "1.000,00"},
        {"label": "E4", "field": "balance", "format": "1.000,00"},
    ],
}


def test_convert(tmp_path):
    config_dir = tmp_path / "config"
    config_dir.mkdir()
    (config_dir / "spec-e.json").write_text(json.dumps(CONVERT_SPEC))
    (config_dir / "broken.json").write_text("{ not json")
    (config_dir / "other.json").write_text(json.dumps({"something": "else"}))
    (tmp_path / "e1.csv").write_text(
        "E1;E2;E3;E4\n01.02.2023;payee-1;-1.234,50;100,00\n02.02.2023;payee-2;5,00;105,00\n"
    )
    (tmp_path / "e2.csv").write_text("E1;E2;E3;E4\n02.02.2023;payee-2;5,00;105,00\n03.02.2023;payee-3;1,00;106,00\n")
    (tmp_path / "x.csv").write_text("X1;X2\n1;2\n")
    output = tmp_path / "out.csv"

    result = CliRunner().invoke(
        cli,
        [
            "convert",
            "-t",
            "tests/fieldspec-banking.json",
            "-c",
            config_dir.as_posix(),
            "-o",
            output.as_posix(),
            *[(tmp_path / name).as_posix() for name in ["e1.csv", "e2.csv", "x.csv"]],
        ],
    )

    assert result.exit_code == 0, result.output
    assert "importing from" in result.output and "yields nothing" in result.output
    assert output.read_text().splitlines() == [
        "date,payee,note,iban,bic,amount,balance",
        "2023-02-01,payee-1,,,,-1234.50,100.00",
        "2023-02-02,payee-2,,,,5.00,105.00",
        "2023-02-03,payee-3,,,,1.00,106.00",
    ]
