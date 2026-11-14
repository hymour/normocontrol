from collections import Counter
from collections.abc import Mapping
import logging
from typing import NamedTuple, SupportsIndex

from services.parser import DocumentInfo
from services.rules import Issue, RULES, IssueCategory

logger = logging.getLogger(__name__)


class Summary(NamedTuple):
    total: SupportsIndex
    by_category: Mapping[IssueCategory, SupportsIndex]


def check_document(parsed: DocumentInfo, standard: str) -> list[dict]:
    all_issues: list[Issue] = []

    for rule_func in RULES:
        try:
            issues = rule_func(parsed, standard)
            if issues:
                all_issues.extend(issues)
        except Exception:
            logger.exception(f"Ошибка в правиле {rule_func.__name__}")

    return all_issues


def summarize(issues: list[Issue]) -> Summary:
    return Summary(
        total=len(issues),
        by_category=Counter(i.category for i in issues),
    )
