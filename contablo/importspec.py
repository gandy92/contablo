from __future__ import annotations

import logging
from typing import Any
from typing import Iterable

import pydantic

from contablo.csv_helper import CsvFileInfo

logger = logging.getLogger(__file__)


class StrictAttribBaseModel(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(extra="forbid")


class ImportMatchRule(StrictAttribBaseModel):
    rule: str
    formats: dict[str, str] = {}  # specify formats for matched fields that require one
    implies: dict[str, str] = {}  # values may append "/"+format where required.
    # Todo: would we need onlyif_all, onlyif_any, notiff_all, notif_any, and which would take precendence?
    onlyif: dict[str, str] = {}  # key: field, value: condition; all conditions must match
    # notif: dict[str, str] = {}  # key: field, value: condition


class ImportColumnSpec(StrictAttribBaseModel):
    """Defines how a certain column is to be used."""

    # Todo: sometimes, the field may depend on the value of other columns,
    #       so eventually we need some basic rule matching

    label: str  # the column label in the file, may be empty
    comment: str = ""
    field: str = ""  # may contain field1+field2, empty if unused  # Todo: Rename to field
    format: str = ""  # field specific configuration
    match: list[ImportMatchRule] | None = []
    map: dict[str, str] | None = {}
    ignore: list[str] | None = []
    samples: list[str] | None = []


class ImportSpec(StrictAttribBaseModel):
    """Specifies how a data table can be imported, i.e. transofrmed to generic import data.

    :param label:
    :param type: account|depot|mixed|snapshot
    :defaults: keys are field identifiers
    """

    label: str
    type: str
    encoding: str | None = None
    skip_lines: int = 0
    delimiter: str = ","
    defaults: dict[str, str] = {}  # values may append "/"+format where required.
    # Todo: formats: dict[str, str] = {}  # default formats for types (number, date, time, datetime) or specific column labels
    columns: list[ImportColumnSpec] = []
    fields: list[dict[str, str]] = []
    transforms: dict[str, str] = {}

    @property
    def column_labels(self):
        return [c.label for c in self.columns]

    def matches(self, other: CsvFileInfo) -> bool:
        """Test if this spec can by used to import the file described by the given csv file info."""
        logger.info("ImportSpec.matches")
        if isinstance(other, CsvFileInfo):
            logger.info(f"Checking {other.source_files}")
            if other.file_encoding != self.encoding:
                logger.info("Spec differs in encoding")
                return False
            for idx, chunk in enumerate(other.chunk_info, 1):
                if chunk.first_line != self.skip_lines + 1:
                    logger.info(f"Chunk {idx} differs in skip_lines")
                    continue
                if chunk.delimiter != self.delimiter:
                    logger.info(f"Chunk {idx} differs in delimiter")
                    continue
                if chunk.columns != self.column_labels:
                    logger.info(f"Chunk {idx} differs in column labels")
                    logger.debug(f"  {chunk.columns=}")
                    logger.debug(f"  {self.column_labels=}")
                    continue
                logger.info(f"Chunk {idx} matches")
                return True

        return False


class ImportSpecRegistry:
    def __init__(self) -> None:
        self.registry: list[ImportSpec] = []
        self.label_source_map: dict[str, str] = {}

    def iter_specs(self) -> Iterable[ImportSpec]:
        yield from self.registry

    def add_import_spec(self, spec: ImportSpec, source: str) -> None:
        self.registry.append(spec)
        self.label_source_map[spec.label] = source

    def query_by_file_info(self, info: CsvFileInfo) -> ImportSpec | None:
        logger.info(f"Scanning {len(self.registry)} specs for {info.source_files}")
        for spec in self.registry:
            logger.debug(f"Next is {spec.label}")
            if spec.matches(info):
                logger.debug(f"Found match: {spec.label}")
                return spec

    def query_source(self, label: str) -> str:
        return self.label_source_map.get(label, None)
