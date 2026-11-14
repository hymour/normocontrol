import logging
from collections import Counter
from services.rules import Issue, RULES

logger = logging.getLogger(__name__)

def check_document(parsed: dict, standard: str) -> list[dict]:
    all_issues: list[Issue] = []
    for rule_func in RULES:
        try:
            issues = rule_func(parsed, standard)
            if issues:
                all_issues.extend(issues)
        except Exception:
            logger.exception(f"Ошибка в правиле {rule_func.__name__}")

    result = []
    for issue in all_issues:
        issue.standard = standard
        result.append(issue.to_dict())

    return result

def summarize(issues: list[dict]) -> dict:
    return {
        "total": len(issues),
        "by_category": dict(Counter(i["category"] for i in issues)),
    }