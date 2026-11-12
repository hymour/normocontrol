from dataclasses import dataclass, asdict

@dataclass
class Issue:
    rule_id: str
    category: str
    message: str
    severity: str = "error"
    paragraph_index: int | None
    standard: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

def error(rule_id: str, category: str, message: str,
          paragraph_index: int | None = None) -> Issue:
    return Issue(
        rule_id=rule_id,
        category=category,
        message=message,
        paragraph_index=paragraph_index,
    )