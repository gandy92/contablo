from __future__ import annotations

import csv
import datetime
import logging

import dateparser

from contablo.codes import is_valid_isin
from contablo.numberformat import NumberFormat

logger = logging.getLogger(__file__)


def is_number(s: str) -> bool:
    """Test if the given string represents a python float or int number."""
    try:
        float(s)
        return True
    except ValueError:
        return False


def guess_separator(header: str) -> str:
    """Gues the most propable separator of a csv header"""
    s = csv.Sniffer().sniff(header)
    # logger.warning(f"{s}")
    return s.delimiter


# Todo: maybe get additional formats from some user configuration?

common_date_formats = {
    "yyyy-mm-dd": "%Y-%m-%d",
    "yyyy/mm/dd": "%Y/%m/%d",
    "yyyymmdd": "%Y%m%d",
    "dd.mm.yyyy": "%d.%m.%Y",
    "dd.mm.yy": "%d.%m.%y",
    "mm/dd/yyyy": "%m/%d/%Y",
    "mm/dd/yy": "%m/%d/%y",
    "dd/mm/yyyy": "%d/%m/%Y",
    "dd/mm/yy": "%d/%m/%y",
    "dd-mm-yyyy": "%d-%m-%Y",
    "dd-mm-yy": "%d-%m-%y",
    "mm-dd-yy": "%m/%d/%y",
    "mm-dd-yyyy": "%m/%d/%Y",
    "yyyy-mm": "%Y-%m",
    "yy-mm-dd": "%y-%m-%d",
    "dd mmm yyyy": "%d %B %Y",
}

common_time_formats = {
    "HH:MM:SS": "%H:%M:%S",
}

common_datetime_formats = {
    "dd.mm.yyyy HH:MM:SS": "%d.%m.%Y %H:%M:%S",
    "dd.mm.yyyy_HH:MM:SS": "%d.%m.%Y_%H:%M:%S",
    "yyyy-mm-dd HH:MM:SS": "%Y-%m-%d %H:%M:%S",
    "yyyy-mm-dd_HH:MM:SS": "%Y-%m-%d_%H:%M:%S",
    "dd mmm yyyy HH:MM:SS": "%d %B %Y %H:%M:%S",
}

DEFAULT_DATE = datetime.datetime.strptime("01:01:01", "%H:%M:%S").date()


def parse_datetime(text: str, datetime_format: str) -> datetime.datetime | None:
    """Parse text for a datetime conforming to the strptime compatible date_format.

    This will first try to use the builtin strptime which conforms more stritctly to the given format.
    Only if that fails, dateparser.parser is used to try parse strings that ptrptime couldn't handle, like
    localised date reprensentations in the form "01. Januar 2012" (german)
    """
    try:
        return datetime.datetime.strptime(text, datetime_format)
    except ValueError:
        pass

    # only try dateparser if there is actual text that hints towards month names:
    if not any(c.isalpha() for c in text) or "%B" not in datetime_format:
        return None
    try:
        return dateparser.parse(text, date_formats=[datetime_format])
    except ValueError as e:
        logger.debug(f"Failed to parse <{text}> with <{datetime_format}>: {e}")
        return None


def parse_date(text: str, date_format: str) -> datetime.date | None:
    """Parsed text for a date conforming to the strptime compatible date_format.

    Returns None instead of raising an expection
    """
    try:
        return parse_datetime(text, date_format).date()
    except (ValueError, AttributeError):
        return None


def parse_time(text: str, time_format: str) -> datetime.time | None:
    """Parsed text for a date conforming to the strptime compatible date_format.

    Returns None instead of raising an expection
    """
    try:
        return parse_datetime(text, time_format).time()
    except (ValueError, AttributeError):
        return None


def is_date_strptime(sample: str, strptime_format: str) -> bool:
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    try:
        # avoid false success due to dateparser.parser being too lax:
        if ":" in sample:
            return None
        dt = parse_datetime(sample, strptime_format)
        return dt.date() != DEFAULT_DATE
    except (ValueError, AttributeError):
        pass

    return False


def is_time_strptime(sample: str, strptime_format: str) -> bool:
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    try:
        # dt = datetime.datetime.strptime(sample, strptime_format)
        dt = parse_datetime(sample, strptime_format)
        return dt.date() == DEFAULT_DATE
    except (ValueError, AttributeError):
        pass

    return False


def is_datetime_strptime(sample: str, strptime_format: str):
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    # avoid false positive due to dateparser.parser being too lax:
    if ":" not in sample:
        return False
    try:
        return parse_datetime(sample, strptime_format) is not None
    except ValueError:
        pass

    return False


def is_date(sample: str, date_format: str):
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    if date_format not in common_date_formats:
        return False
    return is_date_strptime(sample, common_date_formats[date_format])


def is_time(sample: str, time_format: str):
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    if time_format not in common_time_formats:
        return False
    return is_time_strptime(sample, common_time_formats[time_format])


def is_datetime(sample: str, datetime_format: str):
    """Checks if the given date string conforms to the format using dd,MM,yy or yyy"""
    if datetime_format not in common_datetime_formats:
        return False
    return is_datetime_strptime(sample, common_datetime_formats[datetime_format])


def get_date_strptime_from_format(date_format: str):
    assert (
        date_format in common_date_formats
    ), f"Unknown date format {date_format}, expecting one of {common_date_formats.keys()}"
    return common_date_formats.get(date_format)


def get_time_strptime_from_format(time_format: str):
    assert (
        time_format in common_time_formats
    ), f"Unknown time format {time_format}, expecting one of {common_time_formats.keys()}"
    return common_time_formats.get(time_format)


def get_datetime_strptime_from_format(datetime_format: str):
    assert (
        datetime_format in common_datetime_formats
    ), f"Unknown datetime format {datetime_format}, expecting one of {common_datetime_formats.keys()}"
    return common_datetime_formats.get(datetime_format)


def guess_date_format(samples: list[str]) -> str | None:
    for date_format, strptime_format in common_date_formats.items():
        if all([is_date_strptime(s, strptime_format) for s in samples]):
            return date_format
    return None


def guess_time_format(samples: list[str]) -> str | None:
    for time_format, strptime_format in common_time_formats.items():
        if all([is_time_strptime(s, strptime_format) for s in samples]):
            return time_format
    return None


def guess_datetime_format(samples: list[str]) -> str | None:
    for datetime_format, strptime_format in common_datetime_formats.items():
        if all([is_datetime_strptime(s, strptime_format) for s in samples]):
            return datetime_format
    return None


def guess_number_format(samples: list[str]) -> str | None:
    signs, thou_seps, frac_seps = set(), set(), set()
    integer_count = 0
    for sample in samples:
        try:
            format = NumberFormat.from_format(sample)
            if format.is_integer:
                integer_count += 1
                continue
            if format.thou_sep:
                thou_seps.add(format.thou_sep)
            if format.frac_sep:
                frac_seps.add(format.frac_sep)
            if format.sign:
                signs.add(format.sign)
        except ValueError:
            return None

    is_integer = integer_count == len(samples)

    if not is_integer:
        if len(thou_seps) > 1 or len(frac_seps) != 1:
            return None
        if len(thou_seps) > 1 and thou_seps == frac_seps:
            return None

    sign = "" if len(signs) == 0 else ("+" if "+" in signs else "-")
    if is_integer:
        format = NumberFormat(sign, "_", "")
    else:
        format = NumberFormat(sign, "" if len(thou_seps) == 0 else thou_seps.pop(), frac_seps.pop())

    if not all(map(format.is_valid_number, samples)):
        return None
    return format.format


def guess_field_and_format(samples: list[str]) -> tuple[str, str]:
    if not len(samples):
        return "empty", ""

    if all(map(is_valid_isin, samples)):
        return "isin", ""

    if (format := guess_date_format(samples)) is not None:
        return "date", format

    if (format := guess_time_format(samples)) is not None:
        return "time", format

    if (format := guess_datetime_format(samples)) is not None:
        return "datetime", format

    if (format := guess_number_format(samples)) is not None:
        return "number", format

    return "", ""


def format_implicit(tmpl: str, data: dict[str, str]) -> str:
    return tmpl.format_map(data)


def format_tmpl_str(tmpl: str, data: dict) -> str:
    if tmpl is None:
        return ""
    if not isinstance(data, dict):
        return tmpl
    for k, v in data.items():
        if isinstance(v, list):
            while f"{{{k}}}" in tmpl and len(v):
                val = v.pop(0)
                tmpl = tmpl.replace(f"{{{k}}}", val, 1)
            continue

        tmpl = tmpl.replace(f"{{{k}}}", f"{v}", 1)
    return tmpl
