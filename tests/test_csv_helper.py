import pytest

from contablo.csv_helper import EmptyFileError
from contablo.csv_helper import UnknownEncodingError
from contablo.csv_helper import get_file_encoding
from contablo.csv_helper import load_chunked_textfile


def test_load_chunked_textfile():
    chunks = load_chunked_textfile("tests/example-3_chunks_a.csv")  # empty line is chunk delimiter
    assert len(chunks) == 3

    chunks = load_chunked_textfile("tests/example-3_chunks_b.csv")  # line with '""' is chunk delimiter
    assert len(chunks) == 3

    chunks = load_chunked_textfile("tests/example-3_chunks_c.csv")  # empty line is chunk delimiter
    assert len(chunks) == 3


@pytest.mark.parametrize("content", [b"", b"\n", b"  \n\n", b"\r\n\t"])
def test_get_file_encoding_raises_on_empty_file(tmp_path, content):
    path = tmp_path / "empty.csv"
    path.write_bytes(content)
    with pytest.raises(EmptyFileError):
        get_file_encoding(path.as_posix())


def test_get_file_encoding_raises_on_binary_file(tmp_path):
    path = tmp_path / "binary.csv"
    path.write_bytes(bytes(range(256)))
    with pytest.raises(UnknownEncodingError) as exc_info:
        get_file_encoding(path.as_posix())
    assert not isinstance(exc_info.value, EmptyFileError)


def test_encoding_errors_are_lookup_errors():
    assert issubclass(EmptyFileError, UnknownEncodingError)
    assert issubclass(UnknownEncodingError, LookupError)


@pytest.mark.parametrize("content, expected", [(b"a;b\n1;2\n", "us-ascii"), ("ä;b\n".encode(), "utf-8-sig")])
def test_get_file_encoding(tmp_path, content, expected):
    path = tmp_path / "f.csv"
    path.write_bytes(content)
    assert get_file_encoding(path.as_posix()) == expected
