# PLAN — CENTER OF EXCELLENCE School Management System

## Decisions / assumptions
- The folder already contained an older Flask + SQLite prototype (`app.py`, `templates/`, `static/`). It is left untouched; the new system lives in `backend/` and `frontend/`. It can be deleted once the new app is accepted.
- Auth is Django session + CSRF only. Dev is same-origin through the Vite proxy (`/api` -> `127.0.0.1:8000`), so CORS is configured but only needed if you deploy the SPA on another origin.
- `uid` is stored as typed (trimmed) and is unique case-insensitively (DB constraint on `Lower(uid)`). "admin" is reserved for registration only; the admin account itself is created by `create_admin` (uid from `ADMIN_UID`, default prompt).
- `Result.subject` and `User.subject` are normalized (whitespace collapsed, lower-cased) on save so "Maths", " maths " and "MATHS" are the same subject. API output title-cases them.
- Deleting a student cascades to his results. Deleting a teacher keeps results (`teacher` -> NULL) so students' records are not lost; the subject text remains on the result.
- A Section cannot be deleted while any student (FK `PROTECT`) or teacher (checked in the API) is assigned to it.
- Only Approved users may log in. Django `is_active` stays True; `status` is the gate.
- Tests run against PostgreSQL too (Django creates `test_<DB_NAME>`; the DB user needs `CREATEDB`).
- Pagination: `PageNumberPagination`, page size 25 (`?page=`, `?page_size=` up to 100).

## Folder structure
```
backend/
  manage.py  requirements.txt
  config/            settings, urls, wsgi/asgi
  accounts/          User model + manager, auth + registration + admin-user APIs, create_admin
  school/            Section, SiteSettings, sections API, branding API, seed_sections
  results/           Result model, grading, teacher/student/admin result APIs, Excel import, analytics
  reports/           PDF generation (ReportLab) + endpoint
frontend/            Vite + React 18 + Tailwind + Recharts
.env.example  .gitignore  README.md  PLAN.md
```

## Models
- **User**: uid, role, full_name, subject, father_name, mobile, email, status, section(FK, students), sections(M2M, teachers), created_at, is_active, is_staff.
- **Section**: class_name, section; unique together; `label` = "9th-B".
- **Result**: student FK, teacher FK(null), subject, total_marks, obtained_marks, created_at, updated_at; unique(student, subject); CHECK `total_marks > 0 AND 0 <= obtained_marks <= total_marks`.
- **SiteSettings**: single row (pk=1), school_name, logo.
- **Grade scale** `results.grading.grade_for(pct)`: A+ >= 90, A >= 80, B >= 70, C >= 60, D >= 50, else F.

## Endpoints
| Area | Endpoint |
|---|---|
| Auth | GET `/api/auth/csrf/`, POST `/api/auth/login/`, POST `/api/auth/logout/`, GET `/api/auth/me/`, POST `/api/auth/register/` |
| Public | GET `/api/users/public/` (role, uid, name, class/subject, status only), GET `/api/sections/` |
| Admin users | GET `/api/admin/users/`, POST `/api/admin/users/<id>/{approve,block,unblock}/`, DELETE `/api/admin/users/<id>/` |
| Sections | POST `/api/admin/sections/`, DELETE `/api/admin/sections/<id>/` |
| Teacher | GET `/api/teacher/students/`, GET/POST `/api/teacher/results/`, PUT/DELETE `/api/teacher/results/<id>/`, GET `/api/teacher/results/template/`, POST `/api/teacher/results/import/`, GET `/api/teacher/analytics/` |
| Student | GET `/api/student/me/` (profile + marks + totals) |
| Admin results | GET `/api/admin/results/overview/`, GET/POST `/api/admin/results/`, PUT/DELETE `/api/admin/results/<id>/`, GET/POST `/api/admin/branding/` |
| Reports | GET `/api/reports/student/<uid>/pdf/` |

## React routes
`/` and `/register` (register + live table) · `/login` (teacher/student tabs) · `/admin/login` · `/teacher` (students, results, analytics) · `/student` · `/admin/users` · `/admin/sections` · `/admin/overview` · `/admin/results` · `/admin/branding` · `*` 404.

## Phases
1. Backend setup, PostgreSQL, .env, models, migrations, `create_admin`, `seed_sections`.
2. Auth, registration, public users endpoint, admin user APIs + tests.
3. Sections, teacher, student, admin APIs + tests.
4. PDF report.
5. React: register + live table, login, protected routing.
6. Dashboards, admin panel, charts.
7. Polish, README.
