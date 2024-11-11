from __future__ import annotations

import logging

import magic
import pydantic

logger = logging.getLogger(__file__)


class UnknownEncodingError(Exception):
    pass


def get_file_encoding(filename: str) -> str:
    """tries to figure out the correct encoding of the given file"""

    with open(filename, "rb") as f:
        blob = f.read()
        m = magic.Magic(mime_encoding=True)
        encoding = m.from_buffer(blob)
        return "utf-8-sig" if encoding == "utf-8" else encoding

    raise UnknownEncodingError(f"Could not figure out encoding of '{filename}'.")


def load_chunked_textfile(
    filename: str,
    chunk_delimiters: list[str] = None,
    encoding: str = None,
) -> list[list[tuple[int, str]]]:
    """Read one or more chunks from the given file, delimited by empty lines or one of the specified delimiters."""
    chunk_delimiters = chunk_delimiters if chunk_delimiters is not None else ["", '""', "''"]
    chunks = [[]]
    encoding = encoding or get_file_encoding(filename)
    with open(filename, encoding=encoding) as f:
        chunk_num = 0
        for i, row in enumerate(f.readlines(), 1):
            if row.strip() in chunk_delimiters:
                logging.debug(f"New table in {filename} possibly starting at line {i}.")
                chunk_num += 1
                chunks.append([])
                continue
            chunks[chunk_num].append((i, row.strip()))

    logger.info(f"Found {len(chunks)} chunks in '{filename}'")
    return chunks


class ChunkInfo(pydantic.BaseModel):
    """Collects information on data chunks in files.

    A CSV file may contain a number of sections (chunks) delimited by an empty line.  Each chunk comprises information on
    the starting line in the file, the column delimiter, a number of column names and data lines.

    In some files, there may be some sort of meta-data stored as key-value-pair chunks preceding the main table.
    These kind of chunks shall receive a list of empty column names with the same length as the data columns.

    The datalines member may be added to when two ChunkINfo objects are merged.
    """

    delimiter: str
    first_line: int
    columns: list[str]
    datalines: list[str]

    def __eq__(self, other: ChunkInfo) -> bool:
        # chunks are comparable, if the lists column names are identical.
        if self.columns != other.columns:
            return False
        return True

    def add_datalines_from(self, other: ChunkInfo) -> None:
        if self != other:
            raise ValueError("Could not add lines from another format")
        self.datalines += other.datalines


class CsvFileInfo(pydantic.BaseModel):
    source_files: list[str]
    file_encoding: str
    chunk_info: list[ChunkInfo]

    def __eq__(self, other: CsvFileInfo) -> bool:
        if self.file_encoding != other.file_encoding:
            return False
        if self.chunk_info != other.chunk_info:
            return False
        return True

    def add_from(self, other: CsvFileInfo) -> None:
        if self != other:
            raise ValueError("Could not add lines from incompatible file")
        for i in range(0, len(self.chunk_info)):
            self.chunk_info[i].add_datalines_from(other.chunk_info[i])
        self.source_files += other.source_files
