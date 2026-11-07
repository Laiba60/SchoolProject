"""Query helpers and number-crunching shared by the teacher, student, admin and PDF code."""
from accounts.models import Role, Status, User
from school.subjects import sort_results, term_for
from school.utils import normalize_subject

from .grading import GRADES, grade_for, percentage
from .models import Result


def results_qs():
    return Result.objects.select_related("student__section", "teacher")


def teacher_results(teacher):
    """Results of the teacher's own subject for students in the teacher's own sections."""
    return results_qs().filter(subject=teacher.subject, student__section__in=teacher.sections.all())


def teacher_students(teacher):
    return (User.objects.filter(role=Role.STUDENT, status=Status.APPROVED, section__in=teacher.sections.all())
            .select_related("section").order_by("section__class_name", "section__section", "uid"))


def summarize(results):
    """count, average %, grade distribution and per-section average for any iterable of Result."""
    pcts, dist, by_section = [], {g: 0 for g in GRADES}, {}
    for r in results:
        p = r.percentage
        pcts.append(p)
        dist[grade_for(p)] += 1
        by_section.setdefault(r.student.section.label if r.student.section else "-", []).append(p)
    return {
        "count": len(pcts),
        "average": round(sum(pcts) / len(pcts), 2) if pcts else None,
        "grade_distribution": dist,
        "section_averages": [{"section": k, "average": round(sum(v) / len(v), 2)} for k, v in sorted(by_section.items())],
    }


def save_result(student, subject, total, obtained, teacher=None):
    """Create or update the single result of (student, subject)."""
    defaults = {"total_marks": total, "obtained_marks": obtained}
    if teacher is not None:
        defaults["teacher"] = teacher
    return Result.objects.update_or_create(student=student, subject=normalize_subject(subject), defaults=defaults)[0]


def student_report(student):
    """Everything a student dashboard / PDF needs."""
    from school.utils import display_subject
    class_name = student.section.class_name if student.section else ""
    rows = sort_results(Result.objects.filter(student=student), class_name)  # printed report-card order
    total, got = sum(r.total_marks for r in rows), sum(r.obtained_marks for r in rows)
    pct = percentage(got, total)
    return {
        "profile": {"uid": student.uid, "full_name": student.full_name, "father_name": student.father_name,
                    "section": student.section.label if student.section else "",
                    "term": term_for(class_name)},
        "results": [{"subject": display_subject(r.subject), "total_marks": r.total_marks, "obtained_marks": r.obtained_marks,
                     "percentage": r.percentage, "grade": r.grade} for r in rows],
        "total_marks": total, "obtained_marks": got,
        "percentage": pct, "grade": grade_for(pct) if rows else "-",
    }
