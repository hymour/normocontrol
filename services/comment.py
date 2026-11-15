from collections.abc import Sequence

from services.rules import Issue


# TODO: if implementation will use `issues` only as iterable, change
#       type hint from `Sequence` to `Iterable`
def add_comments(file_bytes: bytes, issues: Sequence[Issue]) -> bytes:
    return file_bytes
