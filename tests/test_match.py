import pytest

from contablo.match import check_condition
from contablo.match import check_conditions
from contablo.match import dicts_equal_in_keys
from contablo.match import dicts_equal_without_keys
from contablo.match import match_to_template
from contablo.match import split_after_prefix


@pytest.mark.parametrize(
    "a, b, ignore_keys, expected",
    [
        ({"a": 1}, {"a": 1}, [], True),
        ({"a": 1}, {"a": 2}, [], False),
        ({"a": 1}, {"b": 1}, [], False),
        ({"a": 1, "b": 1}, {"a": 1, "b": 2}, [], False),
        ({"a": 1, "b": 1}, {"a": 1, "b": 2}, ["b"], True),
        ({"a": 1}, {"a": 1, "b": 2}, [], False),
        ({"a": 1}, {"a": 1, "b": 2}, ["b"], True),
        ({"a": 1}, {"a": 1, "b": 2}, [], False),
        ({"a": 1}, {"a": 1, "b": 2}, ["b"], True),
    ],
)
def test_dicts_equal_without_keys(a, b, ignore_keys, expected):
    assert dicts_equal_without_keys(a, b, ignore_keys) == expected


@pytest.mark.parametrize(
    "a, b, compared_keys, expected",
    [
        ({"a": 1}, {"a": 1}, [], True),
        ({"a": 1}, {"a": 2}, [], True),
        ({"a": 1}, {"b": 1}, [], True),
        ({"a": 1}, {"a": 1}, ["a"], True),
        ({"a": 1}, {"a": 2}, ["a"], False),
        ({"a": 1}, {"b": 1}, ["a"], False),
        ({"a": 1, "b": 1}, {"a": 1, "b": 2}, ["a", "b"], False),
        ({"a": 1, "b": 1}, {"a": 1, "b": 2}, ["a"], True),
        ({"a": 1}, {"a": 1, "b": 2}, ["a", "b"], False),
        ({"a": 1}, {"a": 1, "b": 2}, ["a"], True),
        ({"a": 1}, {"a": 1, "b": 2}, ["a", "b"], False),
        ({"a": 1}, {"a": 1, "b": 2}, ["a"], True),
    ],
)
def test_dicts_equal_in_keys(a, b, compared_keys, expected):
    assert dicts_equal_in_keys(a, b, compared_keys) == expected


DIV_PATTERN = "WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}"
BUY_PATTERN = "Kauf WP-Kenn-Nr.: {wkn}, {}, Nominale:  {amount}"

DIV_SAMPLE = "WP-Kenn-Nr.: 858144, Union Pacific Corp., Nominale:  1,0000"
BUY_SAMPLE = "Kauf WP-Kenn-Nr.: 858144, Union Pacific Corp., Nominale:  1,0000"

DIV_SAMPLE_NSPC = "WP-Kenn-Nr.: 858144, Union Pacific Corp., Nominale: 11,0000"
BUY_SAMPLE_NSPC = "Kauf WP-Kenn-Nr.: 858144, Union Pacific Corp., Nominale: 11,0000"


@pytest.mark.parametrize(
    "text, template, strict_whitespace, expected",
    [
        (" 858144, Union Pacific Corp., Nominale:  1,0000", DIV_PATTERN, None, None),
        (DIV_SAMPLE, DIV_PATTERN, None, {"wkn": "858144", "amount": "1,0000"}),
        (BUY_SAMPLE, BUY_PATTERN, None, {"wkn": "858144", "amount": "1,0000"}),
        (DIV_SAMPLE_NSPC, DIV_PATTERN, None, {"wkn": "858144", "amount": "11,0000"}),
        (BUY_SAMPLE_NSPC, BUY_PATTERN, None, {"wkn": "858144", "amount": "11,0000"}),
        (DIV_SAMPLE_NSPC, DIV_PATTERN, True, None),
        (BUY_SAMPLE_NSPC, BUY_PATTERN, True, None),
    ],
)
def test_match_to_template_yields(text, template, strict_whitespace, expected):
    if strict_whitespace is not None:
        assert match_to_template(text, template, strict_whitespace=strict_whitespace) == expected
    else:
        assert match_to_template(text, template) == expected


@pytest.mark.parametrize(
    "prefix, text, expected",
    [
        ("empty", "empty", ["empty"]),
        ("empty", "", []),
        ("equal", "equal:number:0'000.00:1000.0", ["equal", "number", "0'000.00", "1000.0"]),
        ("equal", "equal/number/0'000.00/1000.0", ["equal", "number", "0'000.00", "1000.0"]),
    ],
)
def test_split_after_prefix_yields(prefix, text, expected):
    assert split_after_prefix(prefix, text) == expected


@pytest.mark.parametrize(
    "condition, raw, exception",
    [
        ("kbuiawfvetzrao9hz", None, ValueError),
        ("empty:whatever", "not empty", ValueError),
    ],
)
def test_check_condition_raises(condition, raw, exception):
    with pytest.raises(exception):
        check_condition(condition, raw)


@pytest.mark.parametrize(
    "condition, raw, expected",
    [
        ("empty", None, True),
        ("empty", "", True),
        ("empty", "not empty", False),
        ("notempty", None, False),
        ("notempty", "", False),
        ("notempty", "not empty", True),
        ("is:hello", "hello", True),
        ("is:hello", "Hello", False),
        ("is:hello:i", "Hello", True),
        ("is:hello:i", "there", False),
        ("not:hello:i", "there", True),
        (">:0,00:number:-0.000,00", "-1,00", False),
        (">:0,00:number:0.000,00", "0,00", False),
        (">:0,00:number:0.000,00", "1,00", True),
        (">=:0,00:number:-0.000,00", "-1,00", False),
        (">=:0,00:number:0.000,00", "0,00", True),
        (">=:0,00:number:0.000,00", "1,00", True),
        (">/15.12.2023/date/dd.mm.yyyy", "02.04.2021", False),
        (">/15.12.2023/date/dd.mm.yyyy", "15.12.2023", False),
        (">/15.12.2023/date/dd.mm.yyyy", "16.12.2023", True),
        (">=/15.12.2023/date/dd.mm.yyyy", "02.04.2021", False),
        (">=/15.12.2023/date/dd.mm.yyyy", "15.12.2023", True),
        (">=/15.12.2023/date/dd.mm.yyyy", "16.12.2023", True),
        (">/10:42:57/time/HH:MM:SS", "09:38:29", False),
        (">/10:42:57/time/HH:MM:SS", "10:42:57", False),
        (">/10:42:57/time/HH:MM:SS", "11:38:29", True),
        (">=/10:42:57/time/HH:MM:SS", "09:38:29", False),
        (">=/10:42:57/time/HH:MM:SS", "10:42:57", True),
        (">=/10:42:57/time/HH:MM:SS", "11:38:29", True),
    ],
)
def test_check_condition_yields(condition, raw, expected):
    assert check_condition(condition, raw) == expected


@pytest.mark.parametrize(
    "conditions, field_raw_values, secondary_raw_values, expected",
    [
        ({"value": "empty"}, {"value": ""}, None, True),
        ({"value": "empty"}, {"value": "not empty"}, None, False),
        ({"value": "empty"}, {}, {"value": ""}, True),
        ({"value": "empty"}, {}, {"value": "not empty"}, False),
        ({"value+fees": ">:0,00:number:0.000,00"}, {"value+fees": "-1,00"}, None, False),
        ({"value+fees": ">:0,00:number:0.000,00"}, {"value+fees": "1,00"}, None, True),
    ],
)
def test_check_conditions_yields(conditions, field_raw_values, secondary_raw_values, expected):
    assert check_conditions(conditions, field_raw_values, secondary_raw_values) is expected


@pytest.mark.parametrize(
    "conditions, field_raw_values, secondary_raw_values, expected",
    [
        ({"value": "empty"}, {}, None, KeyError),
        ({"value": "empty"}, {"a": "b"}, None, KeyError),
        ({"value": "empty"}, {"a": "b"}, {"c": "d"}, KeyError),
    ],
)
def test_check_conditions_raises(conditions, field_raw_values, secondary_raw_values, expected):
    with pytest.raises(expected):
        check_conditions(conditions, field_raw_values, secondary_raw_values)
