from __future__ import annotations

import datetime
import logging
from dataclasses import dataclass
from dataclasses import field
from decimal import Decimal
from typing import Any
from typing import Protocol

from contablo.format_helpers import common_date_formats
from contablo.format_helpers import common_datetime_formats
from contablo.format_helpers import common_time_formats
from contablo.format_helpers import is_number
from contablo.format_helpers import parse_datetime
from contablo.numberformat import NumberFormat

logger = logging.getLogger(__file__)


class FieldSpec(Protocol):
    """Interface for a field type specification.

    A field type specification is a class representing a field type that can be converted from a string.
    Objects of a class that implement this protocol have a property name (aka table column name) and a type
    description (e.g. "string" for the StringFieldSpec or "number" for the DecimalFieldSpec).

    The class method convert() allows to convert a string to the native type (e.g. str for StringFieldSpec or
    Decimal for StringFieldSpec), according to an optional format string that informs about how to interpret
    the textual value; see DateFieldSpec or DecimalFieldSpec for examples.  Types that are unsuitable for numeric
    expressions shall set the zero poperty to None.

    Types that are applicable to be used in expressions shall have a "zero" property of the respective type
    representing a zero value, e.g. int(0) or Decimal("0.0").

    Additinal properties may be required for each DieldSpec class to properly initialize and use a class object.
    """

    name: str
    type: str
    zero: Any

    @staticmethod
    def convert(value: str, format: str) -> Any:
        """Convert the text value from provided string format (if applicable) to native type.

        Return type may be None if conversion fails.
        """
        pass


def assert_field_spec_class(cls) -> bool:
    assert isinstance(cls, type), f"{cls} needs to be a class, not an object"
    assert isinstance(getattr(cls, "type", None), str), f"{cls} requires a member named 'type' of type 'str'"
    assert getattr(cls, "convert", None).__class__.__name__ == "function", f"{cls} requires a function 'convert'."


def is_field_spec_class(cls) -> bool:
    try:
        assert_field_spec_class(cls)
        return True
    except AssertionError:
        pass

    return False


@dataclass
class StringFieldSpec:
    name: str
    help: str
    type: str = field(default="string", init=False)
    zero: None = field(default=None, init=False)

    @staticmethod
    def convert(value: str, format: str) -> str:
        return str(value)


@dataclass
class EnumFieldSpec:
    name: str
    help: str
    items: list[str]
    type: str = field(default="enum", init=False)
    zero: None = field(default=None, init=False)

    def convert(self, value: str, format: str) -> str:
        assert value in self.items, f"Unknown item <{value}>, expecting of of {self.items}"
        return value


@dataclass
class IntFieldSpec:
    name: str
    help: str
    type: str = field(default="integer", init=False)
    zero: int = field(default=0, init=False)

    @staticmethod
    def convert(value: str, format: str) -> int:
        return int(value, 10)


@dataclass
class BoolFieldSpec:
    name: str
    help: str
    type: str = field(default="boolean", init=False)
    zero: int = field(default=0, init=False)

    @staticmethod
    def convert(value: str, format: str) -> bool:
        return value.strip().lower() in ("true", "yes", "1")


@dataclass
class DecimalFieldSpec:
    name: str
    help: str
    type: str = field(default="number", init=False)
    zero: Decimal = field(default=Decimal("0"), init=False)

    @staticmethod
    def convert(value: str, format: str) -> Decimal:
        fmt = NumberFormat.from_format(format)
        return Decimal(fmt.normalize(value))


@dataclass
class DateFieldSpec:
    name: str
    help: str
    type: str = field(default="date", init=False)
    zero: None = field(default=None, init=False)

    @staticmethod
    def convert(value: str, format: str) -> datetime.date:
        # see https://docs.python.org/3/library/time.html#time.strptime
        if format != "":
            dt = parse_datetime(value, common_date_formats.get(format, format))
        elif is_number(value):
            ts = float(value)
            # will not allow for dates before 1970-05-08, which is acceptable
            while ts > 1.1e10:
                ts /= 1000.0
            dt = datetime.datetime.fromtimestamp(ts)

        else:
            dt = datetime.datetime.fromisoformat(value)

        return dt.date()  # if dt is not None else None


@dataclass
class TimeFieldSpec:
    name: str
    help: str
    type: str = field(default="time", init=False)
    zero: None = field(default=None, init=False)

    @staticmethod
    def convert(value: str, format: str) -> datetime.time:
        # see https://docs.python.org/3/library/time.html#time.strptime
        dt = datetime.datetime.strptime(value, common_time_formats.get(format, format))
        assert dt.date() == datetime.date(1900, 1, 1)

        return dt.time()


@dataclass
class DateTimeFieldSpec:
    name: str
    help: str
    type: str = field(default="datetime", init=False)
    zero: None = field(default=None, init=False)

    @staticmethod
    def convert(value: str, format: str) -> datetime.datetime:
        # see https://docs.python.org/3/library/time.html#time.strptime
        if format != "":
            dt = parse_datetime(value, common_datetime_formats.get(format, format))
        elif is_number(value):
            ts = float(value)
            # will not allow for dates before 1970-05-08, which is acceptable
            while ts > 1.1e10:
                ts /= 1000.0
            dt = datetime.datetime.fromtimestamp(ts)
        else:
            dt = datetime.datetime.fromisoformat(value)

        return dt


class FieldSpecRegistry:
    """Registry for FieldSpec classes that"""

    def __init__(self):
        self.known_specs: dict[str, type[dataclass]] = {}

    def add(self, spec: type[dataclass]) -> None:
        assert_field_spec_class(spec)
        self.known_specs[spec.type] = spec

    def get_types(self) -> list[str]:
        return list(sorted(self.known_specs.keys()))

    def make_spec_list(self, data: list[dict[str, str]]) -> list[FieldSpec]:
        result: list[FieldSpec] = []
        for idx, item in enumerate(data, 1):
            assert "name" in item, f"Item {idx} requires a field 'name'."
            assert "type" in item, f"Item {idx} reqrequires a field 'type'."
            types = self.get_types()
            name, type = item["name"], item["type"]
            assert (
                item["type"] in types
            ), f"Item {idx} ('{name}') requests unknown type '{type}' - known types are {types}"
            kwargs = item.copy()
            del kwargs["type"]

            try:
                result.append(self.known_specs[type](**kwargs))
            except TypeError as e:
                raise AssertionError(f"Item {idx} ('{name}') cannot be initialized: {e}")

        return result


def add_builtin_fieldspecs_to_registry(registry: FieldSpecRegistry):
    for name, cls in globals().items():
        try:
            if not is_field_spec_class(cls):
                continue
            if not is_field_spec_class(cls):
                continue
            logger.info(f"Adding builtin {name} to fieldspec-registry.")
            registry.add(cls)

        except TypeError:
            pass
