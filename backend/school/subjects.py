"""Subject order of the school's printed Progress Report, per class group.

Single source of truth: the student page, the PDF, the admin list, the Excel template and the
subject suggestions in the forms all use this file.  To change an order, or the term name,
edit only this file.

  Classes 6th, 7th, 8th  : Urdu, English, Math, Science, Islamiyat, History, Geo,
                           Quran Translation, Computer, Drawing
  Classes 9th, 10th      : Math, Physics, Chemistry, Biology / Computer, English, Urdu,
                           Islamiyat, Quran Translation, Pakistan Studies   (2nd Term sheet)
"""
import re

from django.db.models import Case, IntegerField, Q, Value, When

from .utils import normalize_subject

# Printed on the 9th / 10th report ("Term ____"). Change here when the term changes.
SENIOR_TERM_LABEL = "2nd Term"

# key -> (title, class numbers, term label, [(display name, [accepted spellings, lower-case])])
# A slot may accept several spellings; "Biology / Computer" is ONE slot for 9th/10th.
GROUPS = {
    "junior": {
        "title": "Classes 6th – 8th",
        "classes": (6, 7, 8),
        "term": "",
        "slots": [
            ("Urdu", ["urdu"]),
            ("English", ["english"]),
            ("Math", ["math", "maths", "mathematics"]),
            ("Science", ["science", "general science"]),
            ("Islamiyat", ["islamiyat", "islamiat", "islamic studies", "islamyat"]),
            ("History", ["history"]),
            ("Geo", ["geo", "geography"]),
            ("Quran Translation", ["quran translation", "quran", "translation", "translation of quran",
                                   "quran tarjuma", "tarjuma tul quran"]),
            ("Computer", ["computer", "computer science", "computers", "it"]),
            ("Drawing", ["drawing", "art", "arts"]),
        ],
    },
    "senior": {
        "title": "Classes 9th – 10th",
        "classes": (9, 10),
        "term": SENIOR_TERM_LABEL,
        "slots": [
            ("Math", ["math", "maths", "mathematics"]),
            ("Physics", ["physics"]),
            ("Chemistry", ["chemistry"]),
            ("Biology / Computer", ["biology / computer", "biology/computer", "biology", "computer",
                                    "computer science", "computers", "bio"]),
            ("English", ["english"]),
            ("Urdu", ["urdu"]),
            ("Islamiyat", ["islamiyat", "islamiat", "islamic studies", "islamyat"]),
            ("Quran Translation", ["quran translation", "quran", "translation", "translation of quran",
                                   "quran tarjuma", "tarjuma tul quran"]),
            ("Pakistan Studies", ["pakistan studies", "pak studies", "pak study", "pakistan study",
                                  "pakistan studies / pak studies"]),
        ],
    },
}

UNKNOWN_RANK = 99  # subjects not on the card (extra subjects) go after the printed ones

# Regex on Section.class_name ("9th", "10th", "Class 6", ...) for use inside database queries.
_CLASS_RE = {key: r"^[^0-9]*(" + "|".join(str(n) for n in g["classes"]) + r")([^0-9]|$)" for key, g in GROUPS.items()}


def class_number(class_name):
    """6 for '6th' / 'Class 6' / '6-A'; None when there is no number."""
    m = re.search(r"\d+", class_name or "")
    return int(m.group()) if m else None


def group_for(class_name):
    """'junior', 'senior' or None for a class name such as '8th' or '10th'."""
    n = class_number(class_name)
    return next((k for k, g in GROUPS.items() if n in g["classes"]), None)


def term_for(class_name):
    """Term text printed on that class's report ('' when none)."""
    g = group_for(class_name)
    return GROUPS[g]["term"] if g else ""


def _rank_map(group):
    out = {}
    for idx, (_name, spellings) in enumerate(GROUPS[group]["slots"]):
        for s in spellings:
            out.setdefault(s, idx)
    return out


_RANKS = {k: _rank_map(k) for k in GROUPS}


def subject_rank(subject, class_name):
    """Position of the subject on that class's report; UNKNOWN_RANK when it is not listed."""
    g = group_for(class_name)
    if not g:
        return UNKNOWN_RANK
    return _RANKS[g].get(normalize_subject(subject), UNKNOWN_RANK)


def sort_results(results, class_name):
    """Result rows (objects with .subject) in report order; unlisted subjects at the end, A-Z."""
    return sorted(results, key=lambda r: (subject_rank(r.subject, class_name), normalize_subject(r.subject)))


def rank_annotation(class_field="student__section__class_name", subject_field="subject"):
    """A Case() expression giving the report position of a Result row, for QuerySet.order_by()."""
    whens = []
    for group, ranks in _RANKS.items():
        class_q = Q(**{f"{class_field}__iregex": _CLASS_RE[group]})
        for spelling, idx in ranks.items():
            whens.append(When(class_q & Q(**{subject_field: spelling}), then=Value(idx)))
    return Case(*whens, default=Value(UNKNOWN_RANK), output_field=IntegerField())


def sequences():
    """Shape used by GET /api/subjects/ (the frontend shows and suggests these)."""
    return {
        key: {"title": g["title"], "term": g["term"], "subjects": [name for name, _ in g["slots"]]}
        for key, g in GROUPS.items()
    }
