import csv
import datetime
import json
import logging
import time
from pathlib import Path
from typing import Protocol

from contablo.csv_helper import ChunkInfo
from contablo.csv_helper import CsvFileInfo
from contablo.csv_helper import get_file_encoding
from contablo.csv_helper import load_chunked_textfile
from contablo.fields import FieldSpec
from contablo.format_helpers import guess_field_and_format
from contablo.format_helpers import guess_separator
from contablo.importable import ImporTable
from contablo.importspec import ImportColumnSpec
from contablo.importspec import ImportSpec

logger = logging.getLogger(__file__)


class KnowsImportSpec(Protocol):
    def query_by_file_info(self, info: CsvFileInfo) -> ImportSpec: ...


class CsvTemplateGenerator:

    def __init__(self, fields: list[FieldSpec], import_specs_registry: KnowsImportSpec = None) -> None:
        # Todo: accept a repository with known import specs - ???
        self.fields = fields
        self.import_specs_registry = import_specs_registry
        self.input_formats: list[CsvFileInfo] = []
        self.input_specs: dict[str, list[str]] = {}  # maps exisiting ImportSpecs.labels to filenames

    def add_file_info(self, info: CsvFileInfo, ignore_known_specs: bool = False) -> None:
        """Add a CvsFileInfo to the internal list, or merge its filenames and datalines into exisiting ones.

        Existing specs known through the import_specs_registry are ignored and the filenames are instead noted for reporting.
        This behavior can be suppressed by asserting ignore_known_specs.
        """
        assert len(info.source_files) == 1
        if not ignore_known_specs and self.import_specs_registry is not None:
            logger.debug(f"Checking for known specs matching {info.source_files}")
            if spec := self.import_specs_registry.query_by_file_info(info):
                self.input_specs[spec.label] = self.input_specs.get(spec.label, []) + info.source_files
                logger.info(f"Format is already known as import spec <{spec.label}>")
                return

        for format in self.input_formats:
            logger.debug(f"compare file info to that from {format.source_files[0]}")
            if info == format:
                logger.info("Adding more data to previous format")
                format.add_from(info)
                return

        logger.info("Adding new format")
        self.input_formats.append(info)

    def add_files(self, csv_files: list[str]) -> None:
        for csv_file in csv_files:
            self.add_file(csv_file)

    def add_file(self, csv_file: str) -> None:
        """Add a csv file containing transactions to be analyzed.
        Files will be grouped by their csv properties including column labels."""
        encoding = get_file_encoding(csv_file)
        chunk_info = []
        chunks = load_chunked_textfile(csv_file, encoding=encoding)
        # Step 1: analyse chunks, extract separator and column labels, remember line index of header

        for chunk_idx, chunk in enumerate(chunks, 1):
            if not len(chunk):
                print(f"Chunk #{chunk_idx:2d} is empty.")
                continue

            logger.info(f"Chunk #{chunk_idx:2d} starts at line {chunk[0][0]} of {encoding}-encoded file {csv_file}")

            lines = [line for _, line in chunk]

            delimiter = guess_separator(lines[0])

            reader = csv.reader(lines, delimiter=delimiter, quoting=1)
            columns = next(reader)

            # detecting meta-data like this breaks easily: most of te time, there are only two fields (or 3 with the last being empty)
            # but at times, there can be entries in a metadata chunk with more fields
            # maybe it is more feasable to just assume that anything but the last chunk contains metadata rather than a real table.
            if len(columns) == 2 or (len(columns) == 3 and columns[-1] in ["", "''", '""']):
                # this must be metadata
                chunk_info.append(
                    ChunkInfo(delimiter=delimiter, first_line=chunk[0][0], columns=[""] * len(columns), datalines=lines)
                )
            else:
                chunk_info.append(
                    ChunkInfo(delimiter=delimiter, first_line=chunk[0][0], columns=columns, datalines=lines[1:])
                )

        self.add_file_info(CsvFileInfo(source_files=[csv_file], file_encoding=encoding, chunk_info=chunk_info))

    def make_templates(self, output_path_base: str = None, skip_samples: bool = False) -> None:
        """Output import spec template files based on the alanyzed csv files."""
        print(f"Found {len(self.input_formats)} distict file formats:")
        for idx, format in enumerate(self.input_formats, 1):
            print(
                f"  #{idx:2d}: {len(format.source_files)} files, {format.file_encoding} encoded, with {len(format.chunk_info)} chunks."
            )
            for ch, chunk in enumerate(format.chunk_info, 1):
                columns, lines = chunk.columns, chunk.datalines
                print(" " * 7 + f"#{ch:2d}: {len(columns)} columns, {len(lines)} samples")
                if not lines:
                    continue
                columns = chunk.delimiter.join(columns)
                head = columns if len(columns) < 120 else f"{columns[:57]} [..] {columns[-57:]}"
                first = lines[0] if len(lines[0]) < 120 else f"{lines[0][:57]} [..] {lines[0][-57:]}"
                print(" " * 12 + head)
                print(" " * 12 + first)

            spec = self.make_import_spec(format, self.fields, skip_samples=skip_samples)
            if output_path_base is None:
                print("  Not writing output file.")
                continue
            ts = datetime.datetime.fromtimestamp(time.time()).strftime("%Y%m%d_%H%M%S")
            path = Path(output_path_base)
            if path.is_dir():
                output_file = (path / f"new_import_spec-{ts}-{idx:02d}.json").as_posix()
            else:
                output_file = f"{output_path_base}-{ts}-{idx:02d}.json"
            try:
                with open(output_file, "w", encoding="utf8") as f:
                    print("// Generated with CsvTemplateGenerator from these files:", file=f)
                    for filename in format.source_files:
                        print(f"// - {filename}", file=f)
                    # avoid writing \u escaped chars
                    # see https://stackoverflow.com/a/18337754
                    json.dump(spec.model_dump(exclude_unset=True), f, indent=2, ensure_ascii=False)
                print(f"  Template was written to {output_file}")
            except Exception as e:
                print(f"  Failed to write to {output_file}: {e}")

    def make_import_spec(
        self,
        file_info: CsvFileInfo,
        fields: list[FieldSpec],
        skip_samples: bool = False,
    ) -> ImportSpec | None:
        if not file_info.chunk_info:
            return None
        chunk = file_info.chunk_info[-1]

        try:
            # collect samples for each column:
            reader = csv.reader(chunk.datalines, delimiter=chunk.delimiter, quoting=1)
            column_values = {k: set() for k in chunk.columns}
            for row in reader:
                for label, value in zip(chunk.columns, row):
                    if value == "":
                        continue
                    column_values[label].add(value)

            # try to figure out a SpecField type and possible field labels for each column:
            specs = []
            for label in chunk.columns:
                samples = list(column_values[label])
                field_type, format = guess_field_and_format(samples)
                spec = dict(label=label, field=field_type)
                field_hint = ImporTable(fields).compatible_fields(field_type or "string")
                if field_hint:
                    spec["field"] = "|".join(field_hint)

                spec["format"] = format
                if not field_type and not format and not skip_samples:
                    spec["samples"] = list(sorted(samples))

                specs.append(ImportColumnSpec(**spec))

            spec = ImportSpec(  # Todo: Use dependency injection
                label="INSTITUTION-SUBACCOUNT",
                type="account|depot|mixed|snapshot",  # Todo: Application specific, should be used with ImportSpec subclass
                encoding=file_info.file_encoding,
                skip_lines=chunk.first_line - 1,
                defaults={
                    "quote_currency": "EUR"
                },  # Todo: Application specific, should be used with ImportSpec subclass
                columns=specs,
            )
            return spec

        except NotImplementedError:  # Todo: leftover from previous implementation - keep or drop?
            pass
