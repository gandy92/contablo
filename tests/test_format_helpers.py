import datetime

import pytest

from contablo.format_helpers import format_implicit
from contablo.format_helpers import format_tmpl_str
from contablo.format_helpers import guess_date_format
from contablo.format_helpers import guess_datetime_format
from contablo.format_helpers import guess_field_and_format
from contablo.format_helpers import guess_number_format
from contablo.format_helpers import guess_time_format
from contablo.format_helpers import is_date
from contablo.format_helpers import is_datetime
from contablo.format_helpers import is_number
from contablo.format_helpers import is_time
from contablo.format_helpers import parse_date
from contablo.format_helpers import parse_datetime
from contablo.format_helpers import parse_time


@pytest.mark.parametrize(
    "number, expected",
    [
        ("123", True),
        ("-1.23", True),
        ("+1.23e4", True),
        ("abc", False),
        ("", False),
    ],
)
def test_is_number_yields(number, expected):
    assert is_number(number) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("1 Okt 2024 13:05:20", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 10, 1, 13, 5, 20)),
        ("14 Aug 2024 10:22:41", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 8, 14, 10, 22, 41)),
        ("14 Jun 2024 10:28:55", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 6, 14, 10, 28, 55)),
        ("14 Jun 2024 10:29:44", "%d %B %Y %H:%M:%S", datetime.datetime(2024, 6, 14, 10, 29, 44)),
    ],
)
def test_parse_datetime(sample, format, expected):
    assert parse_datetime(sample, format) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("05. Februar 2024", "%d %B %Y", datetime.date(2024, 2, 5)),
        ("07. August 2024", "%d %B %Y", datetime.date(2024, 8, 7)),
        ("07. Mai 2024", "%d %B %Y", datetime.date(2024, 5, 7)),
        ("07. May 2024", "%d %B %Y", datetime.date(2024, 5, 7)),
        ("09. August 2024", "%d %B %Y", datetime.date(2024, 8, 9)),
        ("10. Juli 2024", "%d %B %Y", datetime.date(2024, 7, 10)),
        ("10 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 10)),
        ("11 Jun 2024", "%d %B %Y", datetime.date(2024, 6, 11)),
        ("11 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 11)),
        ("12 Mrz 2024", "%d %B %Y", datetime.date(2024, 3, 12)),
        ("16 Aug 2024", "%d %B %Y", datetime.date(2024, 8, 16)),
        ("16 Okt 2024", "%d %B %Y", datetime.date(2024, 10, 16)),
    ],
)
def test_parse_date(sample, format, expected):
    assert parse_date(sample, format) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("01:02:03", "%H:%M:%S", datetime.time(1, 2, 3)),
        ("01:0203", "%H:%M:%S", None),
    ],
)
def test_parse_time(sample, format, expected):
    assert parse_time(sample, format) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("01/02/03", "mm/dd/yy", True),
        ("13/02/03", "mm/dd/yyyy", False),
        ("01.02.03", "dd.mm.yy", True),
        ("01.02.2003", "mm.dd.yyyy", False),
        ("01.02.03", "mm/dd/yyyy", False),
    ],
)
def test_is_date_yields(sample, format, expected):
    assert is_date(sample, format) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("01:02:03", "HH:MM:SS", True),
        ("13/02/03", "mm/dd/yyyy", False),
    ],
)
def test_is_time_yields(sample, format, expected):
    assert is_time(sample, format) == expected


@pytest.mark.parametrize(
    "sample, format, expected",
    [
        ("2 Nov 2023 15:42:24", "dd mmm yyyy HH:MM:SS", True),
        ("3 Nov 2023 15:59:39", "dd mmm yyyy HH:MM:SS", True),
        ("20 Nov 2023 10:51:39", "dd mmm yyyy HH:MM:SS", True),
        ("24 Jan 2024 14:04:41", "dd mmm yyyy HH:MM:SS", True),
        ("31 Jan 2024 10:49:34", "dd mmm yyyy HH:MM:SS", True),
        ("31 Jan 2024 10:50:25", "dd mmm yyyy HH:MM:SS", True),
        ("6 Feb 2024 12:32:43", "dd mmm yyyy HH:MM:SS", True),
        ("8 Mrz 2024 13:40:31", "dd mmm yyyy HH:MM:SS", True),
        ("4 Jun 2024 21:06:27", "dd mmm yyyy HH:MM:SS", True),
        ("7 Jun 2024 20:31:00", "dd mmm yyyy HH:MM:SS", True),
        ("14 Jun 2024 10:29:44", "dd mmm yyyy HH:MM:SS", True),
        ("14 Jun 2024 10:28:55", "dd mmm yyyy HH:MM:SS", True),
        ("22 Jul 2024 08:01:59", "dd mmm yyyy HH:MM:SS", True),
        ("22 Jul 2024 13:05:33", "dd mmm yyyy HH:MM:SS", True),
        ("25 Jul 2024 21:51:32", "dd mmm yyyy HH:MM:SS", True),
        ("14 Aug 2024 10:22:41", "dd mmm yyyy HH:MM:SS", True),
        ("1 Okt 2024 13:05:20", "dd mmm yyyy HH:MM:SS", True),
        ("2 Okt 2024 15:35:57", "dd mmm yyyy HH:MM:SS", True),
        ("8 Okt 2024 12:41:32", "dd mmm yyyy HH:MM:SS", True),
        ("8 Okt 2024 12:43:21", "dd mmm yyyy HH:MM:SS", True),
        ("8 Okt 2024 12:46:14", "dd mmm yyyy HH:MM:SS", True),
        ("8 Okt 2024 16:10:19", "dd mmm yyyy HH:MM:SS", True),
        ("9 Okt 2024 16:09:18", "dd mmm yyyy HH:MM:SS", True),
        ("14 Okt 2024 13:58:26", "dd mmm yyyy HH:MM:SS", True),
        ("14 Okt 2024 14:00:47", "dd mmm yyyy HH:MM:SS", True),
        ("17 Okt 2024 09:53:04", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 21:57:59", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 22:07:11", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 22:10:40", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 22:31:32", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 22:29:21", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 21:56:52", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 21:55:52", "dd mmm yyyy HH:MM:SS", True),
        ("25 Okt 2024 21:53:37", "dd mmm yyyy HH:MM:SS", True),
        ("01:02:03", "HH:MM:SS", False),
        ("13/02/03", "mm/dd/yyyy", False),
    ],
)
def test_is_datetime_yields(sample, format, expected):
    assert is_datetime(sample, format) == expected


@pytest.mark.parametrize(
    "samples, expected",
    [
        (["01:02:03"], "HH:MM:SS"),
        (["01:0203"], None),
    ],
)
def test_guess_time_format_yields(samples, expected):
    assert guess_time_format(samples) == expected


date_samples_ddmmyyyy = [
    "15.02.2024",
    "20.11.2023",
    "03.11.2023",
    "08.03.2024",
    "01.11.2023",
    "31.01.2024",
    "05.03.2024",
    "04.04.2024",
    "06.02.2024",
    "24.01.2024",
    "02.11.2023",
]

dbyhms_samples_ger = ["1 Okt 2024 13:05:20", "14 Aug 2024 10:22:41", "14 Jun 2024 10:28:55", "14 Jun 2024 10:29:44"]
dby_samples_ger_long = ["05. Februar 2024", "07. August 2024", "07. Mai 2024", "09. August 2024", "10. Juli 2024"]
dby_samples_ger_short = ["10 Okt 2024", "11 Jun 2024", "11 Okt 2024", "12 Mrz 2024", "16 Aug 2024", "16 Okt 2024"]


@pytest.mark.parametrize(
    "samples,  expected",
    [
        (["01/02/03"], "mm/dd/yy"),
        (["01/02/2003"], "mm/dd/yyyy"),
        (["01.02.03"], "dd.mm.yy"),
        (["01.02.2003"], "dd.mm.yyyy"),
        (["01.0203"], None),
        (["01.13.24"], None),
        (date_samples_ddmmyyyy, "dd.mm.yyyy"),
        (dby_samples_ger_long, "dd mmm yyyy"),
        (dby_samples_ger_short, "dd mmm yyyy"),
        (dbyhms_samples_ger, None),
    ],
)
def test_guess_date_format_yields(samples, expected):
    assert guess_date_format(samples) == expected


@pytest.mark.parametrize(
    "samples, expected",
    [
        (["30.04.2024 23:00:41"], "dd.mm.yyyy HH:MM:SS"),
        (["2023-01-04 09:19:16", "2023-01-16 06:56:26"], "yyyy-mm-dd HH:MM:SS"),
        (["01/02/2003"], None),
        (["01.02.03"], None),
        (["01.02.2003"], None),
        (["01.0203"], None),
        (["01.13.24"], None),
        (date_samples_ddmmyyyy, None),
        (dbyhms_samples_ger, "dd mmm yyyy HH:MM:SS"),
    ],
)
def test_guess_datetime_format_yields(samples, expected):
    assert guess_datetime_format(samples) == expected


@pytest.mark.parametrize(
    "samples, expected",
    [
        ([], ("empty", "")),
        (["01:02:03", "23:01:12"], ("time", "HH:MM:SS")),
        (
            ["30.04.2024 23:00:41", "30.04.2024 23:00:43", "30.04.2024 23:00:51", "30.04.2024 23:00:53"],
            ("datetime", "dd.mm.yyyy HH:MM:SS"),
        ),
        (["1", "10", "140", "2"], ("number", "1_000")),
        (
            ["2023-01-04 09:19:16", "2023-01-16 06:56:26", "2023-01-17 15:08:48", "2023-01-18 00:33:37"],
            ("datetime", "yyyy-mm-dd HH:MM:SS"),
        ),
        (dbyhms_samples_ger, ("datetime", "dd mmm yyyy HH:MM:SS")),
        (dby_samples_ger_long, ("date", "dd mmm yyyy")),
        (dby_samples_ger_short, ("date", "dd mmm yyyy")),
    ],
)
def test_guess_field_and_format_yields(samples, expected):
    assert guess_field_and_format(samples) == expected


@pytest.mark.parametrize(
    "samples, expected",
    [
        (["01:02:03", "23:01:12"], None),
        (["+1'745.2", "-2'345.678'9", "32.134234"], "+1'000.00"),
        (["+1.745,2", "-2.345,678.9"], "+1.000,00"),
        (["+1'745.2", "+1.745,2", "-2.345,678.9"], None),
        (["1.00.000,0"], None),
        (["1.00.000.000,000.000.000"], None),
        (["1.000.000.000,000.00.000"], None),
        (["1.000,000.0"], "1.000,00"),
        (["1.000.000,000.000.0"], "1.000,00"),
        (["1.000.000.000,000.000.000.0"], "1.000,00"),
        (["01.12.24"], None),
        (["01.12.2024"], None),
        (["1", "10", "140", "2"], "1_000"),
        (
            [
                "0",
                "0,043977",
                "27,893034",
                "3.229,052385",
                "3.272,771602",
                "38,245964",
                "38,92462",
                "42,73373",
                "43,665435",
                "47,106",
                "480,996",
            ],
            "1.000,00",
        ),
        (
            [
                "0",
                "1,27",
                "1.000",
                "17,01",
                "173,61",
                "189,11",
                "19,78",
                "200",
                "202,02",
                "21,67",
                "425,73",
                "449,93",
                "5.000",
                "50,4",
                "7,83",
                "7.000",
                "75,49",
                "79,86",
                "8,52",
                "80,99",
            ],
            None,
        ),  # TOdo: Should be "1.000,00" but one outlier avoids that.
    ],
)
def test_guess_number_format_yields(samples, expected):
    assert guess_number_format(samples) == expected


@pytest.mark.parametrize(
    "tmpl, data, expected",
    [
        (
            "sub0-{User_ID}-{Account}-{UTC_Time}",
            {"User_ID": "123456789", "UTC_Time": "2021-01-04 09:19:16", "Account": "Sub1"},
            "sub0-123456789-Sub1-2021-01-04 09:19:16",
        ),
        (
            "sub0-{User ID}-{Account}-{Time (UTC)}",
            {"User ID": "123456789", "Time (UTC)": "2021-01-04 09:19:16", "Account": "Sub1"},
            "sub0-123456789-Sub1-2021-01-04 09:19:16",
        ),
    ],
)
def test_format_implicit_yields(tmpl, data, expected):
    assert format_implicit(tmpl, data) == expected


@pytest.mark.parametrize(
    "tmpl, data, expected",
    [
        (None, None, ""),
        (None, {}, ""),
        ("nodict", None, "nodict"),
        ("bare", {"test": "a"}, "bare"),
        ("{missing}", {}, "{missing}"),
        ("{missing}", {"miss": "no miss"}, "{missing}"),
        ("{native}", {"native": "EUR"}, "EUR"),
        ("{asset}", {"asset": ["1st", "2nd"]}, "1st"),
        ("{asset} {a} {asset} {b} {asset}", {"asset": ["1st", "2nd", "3rd"], "a": "A", "b": "B"}, "1st A 2nd B 3rd"),
        ("{asset} {a} {asset} {b} {asset}", {"asset": ["1st", "2nd"], "a": "A", "b": "B"}, "1st A 2nd B {asset}"),
        ("{timestamp}", {"timestamp": datetime.datetime.fromisoformat("2024-01-02 10:22:33")}, "2024-01-02 10:22:33"),
    ],
)
def test_format_tmpl_str(tmpl: str, data: dict, expected: str):
    assert format_tmpl_str(tmpl, data) == expected


@pytest.mark.parametrize(
    "tmpl_list, data, expected",
    [
        (["{asset} {a} {asset} {b} {asset}"], {"asset": ["1st", "2nd"], "a": "A", "b": "B"}, ["1st A 2nd B {asset}"]),
        (["{asset}", "{native}", "{asset}"], {"asset": "A", "native": "B"}, ["A", "B", "A"]),
        (["{asset}", "{native}", "{asset}"], {"asset": ["A", "C"], "native": "B"}, ["A", "B", "C"]),
        (
            ["{asset}", "{native}", "{asset}", "{asset}"],
            {"asset": ["A", "C"], "native": "B"},
            ["A", "B", "C", "{asset}"],
        ),
        (["{asset}", "{native}", "{asset}, {asset}"], {"asset": ["A", "C"], "native": "B"}, ["A", "B", "C, {asset}"]),
        (["{asset}", "{native}", "{asset}, {asset}"], {"asset": ["A", "C", "D"], "native": "B"}, ["A", "B", "C, D"]),
    ],
)
def test_format_tmpl_list_str(tmpl_list: list[str], data: dict, expected: list[str]):
    assert [format_tmpl_str(tmpl, data) for tmpl in tmpl_list] == expected
