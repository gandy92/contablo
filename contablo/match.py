import datetime
from typing import Optional

from contablo.format_helpers import get_date_strptime_from_format
from contablo.format_helpers import get_time_strptime_from_format
from contablo.numberformat import NumberFormat


def dicts_equal_without_keys(a, b, ignore_keys):
    ka = set(a).difference(ignore_keys)
    kb = set(b).difference(ignore_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)


def dicts_equal_in_keys(a, b, compared_keys):
    ka = set(a).intersection(compared_keys)
    kb = set(b).intersection(compared_keys)
    return ka == kb and all(a[k] == b[k] for k in ka)


def match_to_template(text: str, template: str, strict_whitespace: bool = False) -> Optional[dict[str, str]]:
    import re

    pattern = re.escape(template)
    if not strict_whitespace:
        pattern = re.sub(r"(\\\s)+", r"\\s+", pattern)
    pattern = re.sub(r"\\\{\\\}", r".+", pattern)
    pattern = re.sub(r"\\\{(\w+)\\\}", r"(?P<\1>.*)", pattern)
    # print(template, pattern)
    match = re.match(pattern, text)
    return match.groupdict() if match is not None else None


def split_after_prefix(prefix: str, text: str) -> list[str]:
    if text == prefix:
        return [prefix]
    if not text.startswith(prefix):
        return []
    delimiter = text[len(prefix)]
    return text.split(delimiter)


def check_condition_value_is_empty(raw: str, parts: list[str]) -> bool:
    assert len(parts) - 1 == 0, "[]"
    assert parts[0] == "empty"
    return not raw


def check_condition_value_is_not_empty(raw: str, parts: list[str]) -> bool:
    assert len(parts) - 1 == 0, "[]"
    assert parts[0] == "notempty"
    return (raw is not None) and (raw != "")


def check_condition_value_compare(raw: str, parts: list[str]) -> bool:
    assert len(parts) - 1 == 3, "[value, type, format] with type one of [number, date, time, datetime]"
    mode, raw_ref, subtype, format = parts
    assert subtype in ["number", "date", "time", "datetime"], f"unknwon type <{subtype}>"

    if raw is None:
        return False

    if subtype == "number":
        num_fmt = NumberFormat.from_format(format)
        value = float(num_fmt.normalize(raw))
        ref_value = float(num_fmt.normalize(raw_ref))
    elif subtype == "date":
        date_fmt = get_date_strptime_from_format(format)
        value = datetime.datetime.strptime(raw, date_fmt).date()
        ref_value = datetime.datetime.strptime(raw_ref, date_fmt).date()
    elif subtype == "time":
        time_fmt = get_time_strptime_from_format(format)
        value = datetime.datetime.strptime(raw, time_fmt).time()
        ref_value = datetime.datetime.strptime(raw_ref, time_fmt).time()
    else:
        raise NotImplementedError(f"check_condition_value_compare requires implementation for {subtype=}")
    cls = value.__class__
    methods = {"=": cls.__eq__, "!=": cls.__ne__, "<": cls.__lt__, ">": cls.__gt__, "<=": cls.__le__, ">=": cls.__ge__}
    assert mode in methods, f"Unknown condition mode '{mode}'"
    func = methods[mode]
    # print(f"## check if {value} {mode} {ref_value} using {func}")
    return func(value, ref_value)


def check_condition_string_is(raw: str, parts: list[str]) -> bool:
    assert 1 <= len(parts) - 1 <= 2, "[text, [i]]"

    _, text, flags = (parts + [""])[:3]

    assert all([c in "i" for c in flags]), f"Unsupported flag in <{flags}>"

    if "i" in flags:
        raw, text = raw.lower(), text.lower()

    return raw == text


def check_condition_string_is_not(raw: str, parts: list[str]) -> bool:
    return not check_condition_string_is(raw, parts)


def check_condition(cond: str, raw: str) -> list[str]:
    # Todo: maybe put this in a class, allow to query for conditions with syntax (see assert in handlers)
    conditions = [
        ["empty", 0, check_condition_value_is_empty],
        ["notempty", 0, check_condition_value_is_not_empty],
        ["=", 3, check_condition_value_compare],
        ["!=", 3, check_condition_value_compare],
        ["<", 3, check_condition_value_compare],
        [">", 3, check_condition_value_compare],
        ["<=", 3, check_condition_value_compare],
        [">=", 3, check_condition_value_compare],
        ["is", 1, check_condition_string_is],  # value
        ["is", 2, check_condition_string_is],  # value, [i]
        ["not", 1, check_condition_string_is_not],  # value
        ["not", 2, check_condition_string_is_not],  # value, [i]
    ]
    possible_cause = ""
    for type, nargs, func in conditions:
        if not (parts := split_after_prefix(type, cond)):
            continue
        if len(parts) - 1 != nargs:
            possible_cause = f"Expected {nargs} argument{'s' if nargs == 1 else ''} for '{type}', got {parts[1:]}."
            continue
        return func(raw, parts)
    if possible_cause:
        raise ValueError(possible_cause)
    raise ValueError("Unknown condition {type}.")


def check_conditions(
    conditions: dict[str, str],
    primary_raw_values: dict[str, str],
    secondary_raw_values: dict[str, str] | None = None,
) -> bool:
    """Check if the provided raw values meet all conditions. Raises KeyError for unknown condition keys."""
    secondary_raw_values = secondary_raw_values or {}
    for field, cond in conditions.items():
        # might raise a KeyError indicating an unknown field or input key
        if field not in primary_raw_values and field not in secondary_raw_values:
            keys = set(list(primary_raw_values.keys()) + list(secondary_raw_values.keys()))
            raise KeyError(f"Field <{field}> requested when only <{keys}> where given.")
        if not check_condition(cond, primary_raw_values.get(field, secondary_raw_values.get(field, None))):
            return False
    return True
