"""Small helpers shared by several apps (kept free of model imports)."""


def normalize_subject(value):
    """Collapse whitespace and lower-case so 'Maths', ' MATHS ' and 'maths' are one subject."""
    return " ".join((value or "").split()).lower()


def display_subject(value):
    """Human-friendly form of a normalized subject for API output / PDFs."""
    return (value or "").title()
