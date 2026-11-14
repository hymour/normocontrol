from collections.abc import Sequence

from services.rules import Issue


def add_comments(file_bytes: bytes, errors: Sequence[Issue]) -> bytes:
    return file_bytes
