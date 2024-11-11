from __future__ import annotations

from typing import Any
from typing import Callable

import pydantic

from contablo.fields import FieldSpec
from contablo.match import dicts_equal_in_keys


class ImportDatum(pydantic.BaseModel):
    source_lbl: str  # source column label
    raw_value: str
    format: str


class ImporTable:
    """Intermediary table for data to be imported.

    May contain additional metadata found in the import file.

    Import data of the same kind (aka using the same import spec) may be distributed over several
    files, possibly with duplicated entries. These duplicates must be removed in a first step,
    yielding one Importable instance with unique entries.

    Import files originating from the same exporting site may contain aspects of the same
    transactions, e.g. one file containing _value_ and the other _value+fees_, from which
    _fees_ can be calculated. Two or more such Importable instances may be merged yielding
    an Importable instance with unique combined entries.

    Each Importable instance with unique combined entries may be post-processed to interpret
    each entry as to how to create transactions for the main ledger.
    """

    def __init__(self, fields: list[FieldSpec]) -> None:
        self.fields_list: list[FieldSpec] = fields
        self.fields = {t.name: t for t in self.fields_list}
        self.columns = [t.name for t in self.fields_list]  # all of these will be used to check for duplicates
        self.data_vector: list[dict[str, Any]] = []  # see self.columns for valid keys

    def __len__(self) -> int:
        return len(self.data_vector)

    def clone_empty(self) -> ImporTable:
        return ImporTable(self.fields_list)

    def get_columns(self) -> list[str]:
        return [c for c in self.columns]

    def get_data(self) -> list[dict[str, Any]]:
        # create a semi-deep copy:
        return [{k: v for k, v in row.items()} for row in self.data_vector]

    def get_flat_table(
        self,
        convert_func: Callable[[Any], str] | None = None,
        fallback: Any = None,
        include_header: bool = False,
    ) -> list[list[Any]]:
        rows = []
        if include_header:
            rows.append(self.columns)
        for entry in self.data_vector:
            row = []
            for column in self.columns:
                value = entry.get(column, None)
                if value is None:
                    value = fallback
                elif convert_func is not None:
                    value = convert_func(value)
                row.append(value)
            rows.append(row)

        return rows

    def iter_data(self, reversed: bool = False):
        yield from self.data_vector[:: -1 if reversed else 1]

    def compatible_fields(self, field_or_type: str) -> list[str]:
        field_map = {t.name: t for t in self.fields_list}
        if field_or_type in field_map:
            return [field_or_type]
        return [t.name for t in self.fields_list if t.type == field_or_type]

    def add(self, source: str, import_data: dict[str, ImportDatum]) -> None:
        """Add new dataset unless it contains a field "drop"."""
        # Todo: Error handling needs better design, e.g. specifiying source (e.g. "file:line")
        errors = []
        if import_data.get("drop", None) is not None:
            return
        for k, v in import_data.items():
            if k not in self.fields:
                errors.append(f"Unknown field <{k}>: {v}")
            if not isinstance(v, ImportDatum):
                errors.append(f"Implementation error: <{k}> requires type ImportDatum, got: {v}")
        if errors:
            print("** Errors:")
            for error in errors:
                print(f"   {error}")
            return
        data = {"imported_from": source}
        for field, datum in import_data.items():
            try:
                data[field] = self.fields[field].convert(datum.raw_value, datum.format)
            except (AssertionError, ValueError) as e:
                errors.append(f"{e} for {field=} and {datum=}")
        if errors:
            print("** Errors:")
            for error in errors:
                print(f"   {error}")
            raise ImportError("There were errors while adding data")  # raise a more appropriate Exception

        self.data_vector.append(data)

    def merge_in(self, other: ImporTable):
        """Merge another importable into this one while dropping duplicates.

        For duplicate detection, see is_known_entry()"""
        for data in other.iter_data():
            if self.is_known_entry(data):
                continue
            self.data_vector.append(data)

    def is_known_entry(self, data: dict[str, Any]) -> bool:
        """Checks if the provided data is already known.

        Only keys in self.columns are checked; additional keys like imported_from are ignored.
        This allows to identify identical data imported from different files as duplicates.
        """
        # Todo: devise some caching
        for my_data in self.iter_data():
            if dicts_equal_in_keys(my_data, data, self.columns):
                return True
        return False

    # def to_dataframe(self) -> pd.DataFrame:  # on application level: DataFrame(imp.get_data(), columns=im.get_columns())
    #     columns = self.columns + ["imported_from"]
    #     df = pd.DataFrame(self.data_vector)
    #     for lbl in columns:
    #         if lbl not in df:
    #             df[lbl] = pd.NA
    #     return df[columns]
