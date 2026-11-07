"""Excel template and bulk import of results (.xlsx)."""
import io

from django.db import transaction
from openpyxl import Workbook, load_workbook

from accounts.models import Role, User

from .services import save_result, teacher_students

MAX_ROWS = 5000


def build_template(teacher=None):
    """Entry sheet. With a teacher it is pre-filled with HIS students (class order, then roll no),
    so only the two marks columns are left to type. Without one it holds a single example row."""
    wb = Workbook()
    ws = wb.active
    ws.title = "Results"
    ws.append(["Student Name", "Roll No", "Class", "Total Marks", "Obtained Marks"])
    students = list(teacher_students(teacher)) if teacher is not None else []
    if students:
        for s in students:
            ws.append([s.full_name, s.uid, s.section.label])
    else:
        ws.append(["Ali Ahmed", "S-201", "9th-A", 100, 85])
    for col, width in zip("ABCDE", (28, 14, 10, 13, 16)):
        ws.column_dimensions[col].width = width
    ws.freeze_panes = "A2"
    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf


def _roll(v):
    if v is None:
        return ""
    if isinstance(v, float) and v.is_integer():
        v = int(v)  # Excel stores 201 as 201.0
    return str(v).strip()


def _marks(v):
    """Whole-number marks from a cell, or None when it is not one."""
    if isinstance(v, bool):
        return None
    if isinstance(v, (int, float)):
        return int(v) if float(v).is_integer() else None
    if isinstance(v, str) and v.strip().isdigit():
        return int(v.strip())
    return None


def import_results(teacher, file):
    """Validate every row, save the valid ones in ONE transaction. Returns (imported, errors)."""
    try:
        ws = load_workbook(file, read_only=True, data_only=True).active
        it = ws.iter_rows(values_only=True)
        header = next(it, None)
    except Exception:
        raise ValueError("Could not read that file. Upload an .xlsx Excel file.")
    head = [str(c or "").strip().lower() for c in (header or [])]

    def col(word):
        return next((i for i, h in enumerate(head) if word in h), None)

    i_roll, i_tot, i_obt = col("roll"), col("total"), col("obtain")
    if None in (i_roll, i_tot, i_obt):
        raise ValueError("The first row must have the columns: Student Name, Roll No, Total Marks, Obtained Marks.")

    mine = {s.uid.lower(): s for s in teacher_students(teacher)}
    everyone = set(u.lower() for u in User.objects.filter(role=Role.STUDENT).values_list("uid", flat=True))
    need = max(i_roll, i_tot, i_obt) + 1
    valid, errors = [], []
    for n, row in enumerate(it, start=2):
        if n > MAX_ROWS + 1:
            errors.append({"row": n, "message": f"Only the first {MAX_ROWS} rows are read."})
            break
        row = list(row or []) + [None] * need
        if all(c in (None, "") for c in row):
            continue
        roll = _roll(row[i_roll])
        total, got = _marks(row[i_tot]), _marks(row[i_obt])
        if not roll:
            errors.append({"row": n, "message": "Roll No is empty."})
        elif roll.lower() not in everyone:
            errors.append({"row": n, "message": f"Roll No {roll}: no such student."})
        elif roll.lower() not in mine:
            errors.append({"row": n, "message": f"Roll No {roll}: student is not in your sections (or not approved)."})
        elif total is None or got is None:
            errors.append({"row": n, "message": f"Roll No {roll}: marks must be whole numbers."})
        elif total < 1 or got < 0 or got > total:
            errors.append({"row": n, "message": f"Roll No {roll}: obtained marks must be between 0 and total."})
        else:
            valid.append((mine[roll.lower()], total, got))
    with transaction.atomic():
        for student, total, got in valid:
            save_result(student, teacher.subject, total, got, teacher=teacher)
    return len(valid), errors
