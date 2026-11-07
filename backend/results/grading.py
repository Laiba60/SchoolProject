"""Grade scale used everywhere (API, analytics, PDF). Keep this the single source of truth."""

# (minimum percentage, grade) in descending order.
GRADE_SCALE = [(90, "A+"), (80, "A"), (70, "B"), (60, "C"), (50, "D")]
GRADES = [g for _, g in GRADE_SCALE] + ["F"]


def grade_for(percentage):
    """A+ >= 90, A >= 80, B >= 70, C >= 60, D >= 50, F below 50."""
    for minimum, grade in GRADE_SCALE:
        if percentage >= minimum:
            return grade
    return "F"


def percentage(obtained, total):
    """Percentage rounded to 2 places; 0 when total is not positive."""
    if not total or total <= 0:
        return 0.0
    return round(obtained * 100 / total, 2)
