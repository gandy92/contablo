import logging

from contablo.csv_helper import load_chunked_textfile
from contablo.fields import FieldSpecRegistry
from contablo.format_helpers import format_implicit
from contablo.format_helpers import guess_separator
from contablo.importable import ImporTable
from contablo.importable import ImportDatum
from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportSpec
from contablo.importspec import ImportSpecRegistry
from contablo.match import check_conditions
from contablo.match import match_to_template

logger = logging.getLogger(__file__)


class ImportSpecError(Exception):
    pass


class ImportColumnMismatchError(ImportSpecError):
    pass


class ImportSpecExceededError(ImportSpecError):
    """Raised when an input value is not covered by the given import spec"""

    pass


def make_field_import_datum_dict(
    src_lbl: str,
    spec: dict[str, str],
    fmt_sep: str,
    row_dict: dict[str, str] | None = None,
) -> dict[str, ImportDatum]:
    result = {}
    for field, spec in spec.items():
        value, format = spec.split(fmt_sep, 1) if fmt_sep in spec else (spec, "")
        if row_dict is not None:
            value = format_implicit(value, row_dict)
        result[field] = ImportDatum(source_lbl=src_lbl, raw_value=value, format=format)
    return result


def import_csv_with_spec_detection(
    csv_file: str,
    import_spec_registry: ImportSpecRegistry,
    importable_factory: ImporTable,
    field_spec_registry: FieldSpecRegistry,
) -> ImporTable | None:
    result: ImporTable = None
    found_specs = set()
    for spec in import_spec_registry.iter_specs():
        found = None
        try:
            found = import_csv_with_spec(csv_file, spec, importable_factory, field_spec_registry)
        except ImportColumnMismatchError:
            pass
        except Exception as e:
            logger.exception(e)
            print(f"Exception trying {spec.label} on {csv_file}: {e}")
        if not found:
            continue
        result = found
        found_specs.add(spec.label)

    if len(found_specs) == 0:
        print(f"Found no match for {csv_file}")
        return None

    elif len(found_specs) > 1:
        print(f"** Error: More than one specs matches {csv_file}.")
        print(f"** Error: Please restrict to one of {', '.join(found_specs)}")
        return None

    return result


def import_csv_with_spec(
    csv_file: str,
    import_spec: ImportSpec,
    importable_factory: ImporTable,
    registry: FieldSpecRegistry,
) -> ImporTable | None:
    """Import a single csv file with the given spec

    If the file content does not match the spec, the import will fail
    and another specs might be required to succeed.
    """
    chunks = load_chunked_textfile(csv_file)
    for i, chunk in enumerate(chunks, 1):  # chunk is a list of tuples comprising line number and content
        if not len(chunk):
            logging.debug(f"Chunk #{i:2d} is empty.")
            continue

        lines = [line for _, line in chunk]
        first = lines[0] if len(lines[0]) < 120 else f"{lines[0][:57]} [..] {lines[0][-57:]}"
        logging.debug(f"Chunk #{i:2d} comprises {len(lines)} lines; 1st line is:")
        logging.debug(f"          {first}")
        try:
            import csv

            reader = csv.reader(lines, delimiter=guess_separator(first), quoting=1)
            columns = next(reader)
            if columns != [cspec.label for cspec in import_spec.columns]:
                raise ImportColumnMismatchError()
            logging.info("Columns match, proceeding with import.")

            importable: ImporTable = importable_factory()
            importable.add_extra_fields(registry.make_spec_list(import_spec.fields))
            importable.add_transforms(import_spec.transforms)

            logging.debug(f"{columns=}")

            # Todo: Figure out a way to keep track of errors and warnings, including invalid lines
            for line, row in enumerate(reader, 2):
                add_to_importable_using_import_spec(importable, import_spec, row, f"{csv_file.split('/')[-1]}:{line}")

            return importable

        except NotImplementedError:  # Todo: leftover from previous implementation - keep or drop?
            raise

    return None


def add_to_importable_using_import_spec(
    importable: ImporTable,
    import_spec: ImportSpec,
    row: list[str],
    source: str,
) -> None:
    """Add data to an importable object from a single row in a source described by the given import_spec."""
    # Todo: Figure out a way to keep track of errors and warnings, including invalid lines - maybe return some log object?
    logging.debug(f"{source}: {row}")

    columns = [col.label for col in import_spec.columns]
    row_dict = {k: v for k, v in zip(columns, row)}
    columns_resolved: set[str] = set()  # needs to keep track of all columns with valid data source
    columns_mapped: set[str] = set()

    #
    # step 1: use import spec to collect fields and formats; do not yet handle match clauses
    #
    # do not fill in defaults, yet - otherwise we get a warning when a default value is overwritten
    field_data: dict[str, ImportDatum] = {}
    raw: str
    import_spec: ImportColumnSpec
    ignore_labels = []
    for raw, spec in zip(row, import_spec.columns):
        if not raw:
            ignore_labels.append(spec.label)
            columns_resolved.add(spec.label)
            continue
        if spec.ignore and raw in spec.ignore:  # checked before empty to detect unknown ignorable values
            ignore_labels.append(spec.label)
            columns_resolved.add(spec.label)
            continue
        label, format, field = spec.label, spec.format, spec.field
        if not field:
            # column may still provide data through map or match rules
            continue
        if field == "empty":
            if raw:
                print(f"** Error: Expecting <{label}> to be empty, but got <{raw}>")
            ignore_labels.append(spec.label)
            columns_resolved.add(spec.label)
            continue
        if field in field_data:
            prev = field_data[field].source_lbl
            print(f"** Warning: column {label} redefines field {field} already defined by {prev}")
        if spec.map:
            if raw in spec.map:
                from_raw, raw = raw, spec.map.get(raw)
                logger.debug(f"mapping {source}/{spec.label} from {from_raw} to {raw}")
                columns_mapped.add(spec.label)

        field_data[field] = ImportDatum(source_lbl=label, raw_value=raw, format=format)
        columns_resolved.add(label)

    logging.debug(f"***** {field_data=}")

    #
    # step 2: handle match clauses separately. only-if statements may only use data from step 2
    #
    match_results: dict[str, ImportDatum] = {}
    for raw, spec in zip(row, import_spec.columns):
        if spec.label in ignore_labels:
            continue
        match_groups: list[dict[str, str]] = []
        if not spec.match:
            continue
        for rule_idx, rule in enumerate(spec.match):
            data = match_to_template(raw, rule.rule)
            if data is None:  # None is no match, {} is a match but without data (e.g. with implies)
                logger.warning(f"no data for {raw=} {rule=}")
                continue  # this is normal, only one rule should match
            logging.debug(f"    ! found match with {data=}")
            if rule.onlyif:
                field_dict = {k: v.raw_value for k, v in field_data.items()}
                if not check_conditions(rule.onlyif, field_dict, row_dict):
                    print(f"** Warning: dropping match #{rule_idx} due to onlyif condition not met.")
                    continue
            match_data = {}
            for k, v in data.items():
                match_data[k] = ImportDatum(source_lbl=k, raw_value=v, format=rule.formats.get(k, ""))
            for k, v in make_field_import_datum_dict("(matched rule)", rule.implies, "/", row_dict).items():
                # v.raw_value = format_implicit(v.raw_value, row_dict)  # Todo: if still required, find a better way
                match_data[k] = v
            match_groups.append(match_data)
            # logging.debug(f"      -> {match_groups}")

        if (
            spec.match and not match_groups and spec.label not in columns_mapped
        ):  # and spec.label not in columns_resolved:
            print(f"** {spec.match=}")
            print(f"** {match_groups=}")
            raise ImportSpecExceededError(f"Input spec for {source}/{spec.label} does not cover value; {raw}")

        #
        # step 3: check for clashes between all match clauses
        #
        if len(match_groups):
            if len(match_groups) > 1:
                print(f"** Warning: Multiple matches in {source} column {spec.label}. Will use first match.")
            # logging.debug("      -> {match_groups[0]}")
            for field, value in match_groups[0].items():
                if field in match_results:
                    prev = match_results[field].source_lbl
                    print(f"** Warning: matched rule redefines field {field} already defined by {prev}")
                match_results[field] = value

    #
    # step 4: merge data from step 3 into step 4, starting with defaults
    #

    merged_data = make_field_import_datum_dict("(defaults)", import_spec.defaults, "/", row_dict)
    merged_data.update(field_data)
    merged_data.update(match_results)
    # logging.debug("    >", merged_data)

    #
    # step 5: pass field/value/format tuples into importable
    # importable.feed_data(series.to_dict(), spec)
    #
    importable.add(f"{import_spec.label}:{source}", merged_data)


class ImportColumnConfigError(Exception):
    pass
