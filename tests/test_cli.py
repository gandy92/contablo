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
