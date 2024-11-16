import csv
import json
import logging
from pathlib import Path

import click
import pydantic

from contablo.csvimporter import import_csv_with_spec_detection
from contablo.csvtmplgen import CsvTemplateGenerator
from contablo.fields import FieldSpecRegistry
from contablo.fields import add_builtin_fieldspecs_to_registry
from contablo.importable import ImporTable
from contablo.importablemerge import LeftRightMatchRule
from contablo.importablemerge import importable_merge
from contablo.importspec import ImportSpec
from contablo.importspec import ImportSpecRegistry

logger = logging.getLogger(__file__)
log_levels = [logging.ERROR, logging.WARNING, logging.INFO, logging.DEBUG]


def fill_import_spec_registry(dir_or_file: str, registry: ImportSpecRegistry) -> None:
    import glob

    if not dir_or_file:
        return
    path = Path(dir_or_file)

    file_list = glob.glob((path / "*.json").as_posix()) if path.is_dir() else [dir_or_file]
    for import_config_file in file_list:

        try:
            with open(import_config_file) as f:
                data = json.load(f)
                if not all([key in data for key in ["label", "encoding", "type"]]):
                    logger.warning(f"Skipping {import_config_file}: Not a valid ImportSpec configuration.")
                    continue

                config = ImportSpec(**data)
                registry.add_import_spec(config, import_config_file)

        except json.JSONDecodeError:
            logger.warning(f"Skipping {import_config_file}: Not a valid JSON file.")
        except pydantic.ValidationError as e:
            print(f"Error when trying to initialize import spec from {import_config_file}:")
            from pprint import pprint

            pprint(e.errors())
        except Exception as e:
            logger.exception(e)


@click.group(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True)
def cli(verbose):
    """CLI tool to the ConTabLo python package."""
    logging.basicConfig(
        format="%(asctime)s.%(msecs)03d %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d_%H:%M:%S",
        level=log_levels[min(verbose, len(log_levels) - 1)],
    )


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True, default=None)
@click.option(
    "-t",
    "--target-spec",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="JSON file with target table specs.",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Location of the import spec. May be one single json file or a directory with several config files.",
)
@click.option(
    "-o",
    "--output-base",
    type=str,
    help="Write template to this directory (default: location of input file)",
)
@click.option(
    "-s/-S",
    "--samples/--no-samples",
    default=True,
    help="Decide wheter to include samples in the template or not",
)
@click.argument("csv-files", nargs=-1)
def mk_import_tmpl(
    verbose: int | None, csv_files: list[str], target_spec: str, config: str, output_base: str, samples: bool
):
    """Create an input configuration template for the given CSV file(s)."""
    if verbose is not None:
        logging.getLogger().setLevel(log_levels[min(verbose, len(log_levels) - 1)])

    fields = []

    if target_spec is not None:
        # Initialize target table's field specs from json file. See specs/fieldspec-banking.json for an example.
        # Refer to contablo.fields.ImportSpec subclasses for available types and attributes.
        with open(target_spec) as target_spec_file:
            fieldspecs = FieldSpecRegistry()
            add_builtin_fieldspecs_to_registry(fieldspecs)
            fields = fieldspecs.make_spec_list(json.load(target_spec_file))

    registry = ImportSpecRegistry()
    fill_import_spec_registry(config, registry)

    csv_files = list(csv_files)

    generator = CsvTemplateGenerator(fields, registry)
    generator.add_files(csv_files)
    generator.make_templates(output_path_base=output_base, skip_samples=not samples)


cli.add_command(mk_import_tmpl)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True, default=None)
@click.option(
    "-o",
    "--output-base",
    type=str,
    help="Write schema to this directory (default: location of input file)",
)
@click.argument("schema", nargs=-1)
def mk_schema(verbose: int | None, output_base: str, schema: str):
    """Create a JSON schema for validation of JSON based config files."""
    # Todo: Add a way to also include valid field names in the schema
    if verbose is not None:
        logging.getLogger().setLevel(log_levels[min(verbose, len(log_levels) - 1)])

    schema: list[str] = list(set(schema))
    known_schemas: dict[str, pydantic.BaseModel] = {
        "ImportSpec": ImportSpec,
    }

    for sch in schema:
        if sch not in known_schemas:
            print(f"Unknown schema '{sch}', choose one of {known_schemas.keys()}")
            continue
        data = known_schemas[sch].model_json_schema()
        filename = f"{output_base}{sch.lower()}.json"
        print(f"Writing schema for <{known_schemas[sch].__name__}> to {filename} ...")
        with open(filename, "w") as f:
            json.dump(data, f, indent=2)


cli.add_command(mk_schema)


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("-v", "--verbose", count=True, default=None)
@click.option(
    "-t",
    "--target-spec",
    required=True,
    type=click.Path(exists=True, file_okay=True, dir_okay=False),
    help="JSON file with target table specs.",
)
@click.option(
    "-c",
    "--config",
    type=click.Path(exists=True, file_okay=True, dir_okay=True),
    help="Location of the import spec. May be one simngle json file or a directory with several config files.",
)
@click.option(
    "-o",
    "--output-file",
    type=str,
    help="Export merged imported data to this file.",
)
@click.argument("csv-files", nargs=-1, required=True, type=click.Path(exists=True, file_okay=True, dir_okay=False))
def convert(verbose: int | None, csv_files: list[str], target_spec: str, config: str, output_file: str):
    """Load the given CSV file(s) based on their configurations and write resulting table(s)."""
    if verbose is not None:
        logging.getLogger().setLevel(log_levels[min(verbose, len(log_levels) - 1)])

    registry = ImportSpecRegistry()
    fill_import_spec_registry(config, registry)

    # Initialize target table's field specs from json file. See specs/fieldspec-banking.json for an example.
    # Refer to contablo.fields.ImportSpec subclasses for available types and attributes.
    with open(target_spec) as target_spec_file:
        field_spec_registry = FieldSpecRegistry()
        add_builtin_fieldspecs_to_registry(field_spec_registry)
        fields = field_spec_registry.make_spec_list(json.load(target_spec_file))

    result = ImporTable(fields)
    for csv_file in csv_files:
        importable = import_csv_with_spec_detection(csv_file, registry, result.clone_empty, field_spec_registry)
        if not importable:
            print(f"--- importing from {csv_file} yields nothing ---")
            continue
        result = importable_merge(importable, result, [LeftRightMatchRule({}, ["imported_from"])])
        print(f"--- importing from {csv_file} with {len(importable)} entries results in {len(result)} after merge ---")

    if output_file is not None:
        print("Exporting merged data...")
        with open(output_file, "w") as csv_file:
            csv_writer = csv.writer(csv_file)
            csv_writer.writerows(result.get_flat_table(convert_func=str, fallback="", include_header=True))


cli.add_command(convert)
