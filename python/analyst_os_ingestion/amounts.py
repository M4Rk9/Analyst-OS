"""Parse explicit reported amounts without loading PDF or database dependencies."""

import re
from decimal import Decimal, InvalidOperation

GLYPHS = str.maketrans("ϬϭϮϯϰϱϲϳϴϵ", "0123456789")


def printed_amount(text: str) -> Decimal | None:
    """Only explicit numeric text; dashes and footnoted amounts remain unavailable."""
    value = re.sub(r"[,\s]", "", text.translate(GLYPHS))
    if not re.fullmatch(r"(?:-?\d+(?:\.\d+)?|\(\d+(?:\.\d+)?\))", value):
        return None
    if value.startswith("("):
        value = "-" + value[1:-1]
    try:
        return Decimal(value)
    except InvalidOperation:
        return None

