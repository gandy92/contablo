from contablo.csv_helper import load_chunked_textfile


def test_load_chunked_textfile():
    chunks = load_chunked_textfile("tests/example-3_chunks_a.csv")  # empty line is chunk delimiter
    assert len(chunks) == 3

    chunks = load_chunked_textfile("tests/example-3_chunks_b.csv")  # line with '""' is chunk delimiter
    assert len(chunks) == 3

    chunks = load_chunked_textfile("tests/example-3_chunks_c.csv")  # empty line is chunk delimiter
    assert len(chunks) == 3
