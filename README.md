# CENTER OF EXCELLENCE – School Management System

Django REST + PostgreSQL backend, React (Vite + Tailwind) frontend.

```
backend/          Django project (accounts, school, results, reports)
frontend/         React app
reference-flask/  the old Flask prototype (not used; delete when you like)
PLAN.md           design decisions     DEPLOY.md  how to put it online
```

## What it does
- **Register page** (teacher / student tabs) with a live users table; accounts start as *Pending*.
- **Admin** approves / blocks / deletes users, creates classes and sections, sees every teacher's results,
  adds / edits / deletes results, uploads the school logo.
- **Teacher** sees students of his sections, uploads results (manual or Excel), sees average, grade distribution, section averages.
- **Student** sees only his own result and downloads a PDF with logo and watermark.
- **Logo** (Punjab Daanish Schools & Centres of Excellence) is the faded background of the home/register and login pages (`frontend/public/logo.png`, strength in `frontend/src/components/LogoBackdrop.jsx`).
- **Subject order** follows the printed Progress Report: 6th–8th = Urdu, English, Math, Science, Islamiyat, History, Geo, Quran Translation, Computer, Drawing; 9th–10th = Math, Physics, Chemistry, Biology / Computer, English, Urdu, Islamiyat, Quran Translation, Pakistan Studies (printed with “2nd Term”). It is used on the student page, PDF and admin results list. To change the order or the term name edit only `backend/school/subjects.py`.
- The teacher's Excel template comes pre-filled with the teacher's own students.
- Grades: A+ ≥ 90, A ≥ 80, B ≥ 70, C ≥ 60, D ≥ 50, F below 50. Marks are whole numbers.

## Run on Windows (first time)
Install **Python 3.11+** (tick "Add to PATH"), **Node.js LTS** and **PostgreSQL**.

1. Create the database (SQL Shell / `psql -U postgres`):
```
CREATE DATABASE coe_school;
CREATE USER coe_user WITH PASSWORD 'your_password';
ALTER DATABASE coe_school OWNER TO coe_user;
ALTER USER coe_user CREATEDB;
```
2. Backend (first terminal):
```
cd backend
copy .env.example .env          (then open .env and set DJANGO_SECRET_KEY and DB_PASSWORD)
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py create_admin
python manage.py seed_sections
python manage.py runserver
```
3. Frontend (second terminal):
```
cd frontend
npm install
npm run dev
```
4. Open **http://localhost:5173**. Admin login: http://localhost:5173/admin/login (the ID and password you gave to `create_admin`).

Next times you only need `.venv\Scripts\activate` + `python manage.py runserver`, and `npm run dev`.

## Tests
```
cd backend
.venv\Scripts\activate
pytest
```
(needs `CREATEDB` on `coe_user`, see step 1; Django makes and removes a `test_coe_school` database.)

## Try it
1. Register a teacher and a student on the home page. 2. Log in as admin and press **Approve** in the table.
3. Log in as teacher, upload a result (or use the Excel template). 4. Log in as student and download the PDF.

## Notes and limits
- Anyone can register with any ID; the Admin approval step is the check that the ID is real.
- The live table is public (names, IDs, class). Mobile and email are never shown there.
- Uploaded logo is stored in `backend/media/`. Back it up together with the database.
- Production: see **DEPLOY.md**.
