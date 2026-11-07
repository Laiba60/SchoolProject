# CENTER OF EXCELLENCE – Frontend (React + Vite + Tailwind)

Put this folder next to `backend/` (so you have `backend/` and `frontend/`).

## Run (Windows)
1. Start the Django backend first: `cd backend`, `.venv\Scripts\activate`, `python manage.py runserver` (port 8000).
2. In a second terminal:
```
cd frontend
npm install
npm run dev
```
3. Open http://localhost:5173 (always use this address, not port 8000). Vite forwards `/api` and `/media` to Django, so session cookies and CSRF work without CORS.

Production build: `npm run build` (output in `dist/`).

## Pages
`/register` (tabs + live users table) · `/login` · `/admin/login` · `/teacher` · `/student` · `/admin/users|sections|overview|results|branding`

## API contract this frontend expects
Lists may be plain arrays or DRF-paginated `{results: [...]}`. Errors: DRF style `{field: ["msg"]}` or `{detail: "msg"}`.

| Endpoint | Request | Response |
|---|---|---|
| GET `/api/auth/csrf/` | | sets `csrftoken` cookie |
| POST `/api/auth/login/` | `{uid, password, role}` | user object (below); 400/403 with `{detail}` for wrong password, Pending, Blocked, or role mismatch |
| POST `/api/auth/logout/` | | 204/200 |
| GET `/api/auth/me/` | | user object, or 401/403 when logged out |
| POST `/api/auth/register/` | teacher: `{role, uid, full_name, subject, mobile, email, password, confirm_password, sections: [sectionId]}`; student: same without subject/sections plus `father_name, section: sectionId` | 201; field errors as `{uid: [...]}` |
| GET `/api/users/public/` | `?page_size=100` | `[{id, role, uid, name, info, status}]` (no email/mobile) |
| GET `/api/sections/` | | `[{id, label, class_name, section}]` |
| POST `/api/admin/users/<id>/approve\|block\|unblock/`, DELETE `/api/admin/users/<id>/` | | 200/204 |
| POST `/api/admin/sections/` | `{class_name, sections: ["A","B"]}` (`[""]` = class without section) | 201 |
| DELETE `/api/admin/sections/<id>/` | | 204, or 400 `{detail}` if in use |
| GET `/api/teacher/students/` | | `[{uid, full_name, section (label), father_name}]` |
| GET/POST `/api/teacher/results/`, PUT/DELETE `/api/teacher/results/<id>/` | `{student_uid, total_marks, obtained_marks}` | result object (below) |
| GET `/api/teacher/results/template/` | | `.xlsx` download |
| POST `/api/teacher/results/import/` | multipart `file` | `{imported: n, errors: [{row, message}]}` |
| GET `/api/teacher/analytics/` | | `{count, average, grade_distribution: {"A+": n, ...}, section_averages: [{section, average}]}` |
| GET `/api/student/me/` | | `{profile: {uid, full_name, section, father_name}, results: [{subject, total_marks, obtained_marks, percentage, grade}], total_marks, obtained_marks, percentage, grade}` |
| GET `/api/admin/results/overview/` | | `[{teacher_uid, teacher_name, subject, count, average, grade_distribution, section_averages}]` |
| GET/POST `/api/admin/results/`, PUT/DELETE `/api/admin/results/<id>/` | list filters: `search, section (label), subject, teacher`; body `{student_uid, subject, total_marks, obtained_marks}` | result object |
| GET `/api/admin/branding/` | | `{school_name, logo_url}` |
| POST `/api/admin/branding/` | multipart `school_name`, optional `logo` | updated branding |
| GET `/api/reports/student/<uid>/pdf/?dl=1` | | PDF (browser navigation, session cookie) |

**User object** (login and `/me/`): `{id, uid, role, full_name, subject, sections: ["9th-A", ...]}` where `subject`/`sections` are for teachers.

**Result object**: `{id, student_uid, student_name, section, subject, teacher_name, total_marks, obtained_marks, percentage, grade}`.

If your backend names a field differently, change it in the matching page under `src/pages/` (or ask Claude Code to align the serializers with this table).
