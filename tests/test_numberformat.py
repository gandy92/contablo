import pytest

from contablo.numberformat import NumberFormat


@pytest.mark.parametrize(
    "sample, expected",
    [
        ("+1000.0", NumberFormat("+", "", ".")),
        ("1000,0", NumberFormat("", "", ",")),
        ("+1_000.0", NumberFormat("+", "_", ".")),
        ("1.000,0", NumberFormat("", ".", ",")),
        ("+1,000.000,000", NumberFormat("+", ",", ".")),
        ("1'000,000'0", NumberFormat("", "'", ",")),
        ("0", NumberFormat("", "_", "")),
        ("0000", NumberFormat("", "_", "")),
        ("2960", NumberFormat("", "_", "")),
        ("0_000", NumberFormat("", "_", "")),
    ],
)
def test_number_format_from_format_yields(sample, expected):
    assert NumberFormat.from_format(sample) == expected


@pytest.mark.parametrize(
    "sample, exception",
    [
        ("1_000.000.000_000", ValueError),
    ],
)
def test_number_format_from_format_raises(sample, exception):
    with pytest.raises(exception):
        NumberFormat.from_format(sample)


@pytest.mark.parametrize(
    "sign, thou_sep, frac_sep, trailing_sign, expected",
    [
        ("+", "", ".", None, False),
        ("-", ".", ",", None, False),
        ("+", "", ".", True, False),
        ("-", ".", ",", True, False),
        ("", "'", ".", None, False),
        ("", "_", ".", None, False),
        ("", "_", "", None, True),
    ],
)
def test_number_format_property_is_integer_yields(sign, thou_sep, frac_sep, expected, trailing_sign):
    if trailing_sign is not None:
        assert NumberFormat(sign, thou_sep, frac_sep, trailing_sign).is_integer == expected
    else:
        assert NumberFormat(sign, thou_sep, frac_sep).is_integer == expected


@pytest.mark.parametrize(
    "sign, thou_sep,frac_sep, trailing_sign, expected",
    [
        ("+", "", ".", None, "+1000.00"),
        ("-", ".", ",", None, "-1.000,00"),
        ("+", "", ".", True, "1000.00+"),
        ("-", ".", ",", True, "1.000,00-"),
        ("", "'", ".", None, "1'000.00"),
        ("", "_", ".", None, "1_000.00"),
    ],
)
def test_number_format_property_format_yields(sign, thou_sep, frac_sep, expected, trailing_sign):
    if trailing_sign is not None:
        assert NumberFormat(sign, thou_sep, frac_sep, trailing_sign).format == expected
    else:
        assert NumberFormat(sign, thou_sep, frac_sep).format == expected


@pytest.mark.parametrize(
    "format, sample, expected",
    [
        ("+1'000.0", "a", False),
        ("+1'000.0", "+2'345,67", False),
        ("+1'000.0", "+2_345.678", False),
        ("+1'000.0", "-2_345.678", False),
        ("-1'000.0", "-1.0", True),
        ("-1'000.0", "1.0", True),
        ("-1'000.0", "+1.0", True),
        ("+1'000.0", "-1.0", True),
        ("+1'000.0", "1.0", True),  # could be False?
        ("+1'000.0", "+1.0", True),
        ("+1'000.0", "+1'00'000.0", False),
        ("+1000.0", "+100000.0", True),
        ("+1000.0", "20", True),  # accept an int when format suggests decimal
        ("0", "+100000.0", False),
        ("0", "100000", True),
        ("0_000", "100000", True),
        ("0", "100_000", True),
        ("2960", "1_000.00", False),
        ("1.000,00", "1.000", True),
    ],
)
def test_number_format_is_valid_number_yields(format, sample, expected):
    assert NumberFormat.from_format(format).is_valid_number(sample, raise_on_fail=False) == expected


@pytest.mark.parametrize(
    "format, sample, expected",
    [
        ("+1'000.0", "-1'000.000'0", "-1000.0000"),
        ("+1'000.0", "+1'000.000'0", "1000.0000"),
        ("+1'000.0", "-1'000.000'0", "-1000.0000"),
        ("+1'000.0", "-1'000.000'0", "-1000.0000"),
        ("+1'000.0", "-1'000.000'0", "-1000.0000"),
        ("0", "123", "123"),
    ],
)
def test_number_format_normalize_yields(format, sample, expected):
    assert NumberFormat.from_format(format).normalize(sample) == expected


@pytest.mark.parametrize(
    "format, sample, exception",
    [
        ("+1'000.0", "-1_000.000_0", ValueError),
    ],
)
def test_number_format_normalize_raises(format, sample, exception):
    with pytest.raises(exception):
        NumberFormat.from_format(format).normalize(sample)
