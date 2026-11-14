from dataclasses import dataclass, asdict

@dataclass
class Issue:
    rule_id: str
    category: str
    message: str
    severity: str = "error"
    paragraph_index: int | None = None
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

# --- константы ГОСТ
GOST_FONT = "Times New Roman"
GOST_FONT_SIZE_PT_MIN = 12
GOST_INTERVAL = 1.5
GOST_MARGINS_MM = {"left": 30, "right": 15, "top": 20, "bottom": 20}

# --- константы МУ ПО
MUPO_FONT = "Times New Roman"
MUPO_FONT_SIZE_PT = {12, 14}
MUPO_INTERVAL = 1.5
MUPO_PARA_INDENT_CM = 1.25
MUPO_MARGINS_MM = {"left": 30, "right": 10, "top": 20, "bottom": 20}

# --- функции проверки
# --- оформления документа
def check_margins(parsed: dict, standard: str) -> list[Issue]:
    issues = []
    margins = GOST_MARGINS_MM if standard == "GOST_732" else MUPO_MARGINS_MM

    for s in parsed.get("sections", []):
        for name, expected_mm in margins.items():
            actual_cm = s.get(f"{name}_margin_cm")
            if actual_cm is None:
                continue
            actual_mm = actual_cm * 10
            if abs(actual_mm - expected_mm) > 1:
                issues.append(error(
                    rule_id=f"document.margins.{name}",
                    category="document",
                    message=f"Поле {name} = {actual_mm:.0f} мм, ожидается {expected_mm} мм"
                ))
    return issues

# --- финал
def _iter_runs(parsed: dict):
    for para in parsed.get("paragraphs", []):
        for run in para.get("runs", []):
            if run.get("text", "").strip():
                yield para, run

RULES = [
    check_margins,
]