# Product Requirements Document (PRD)

## 1. Overview

**Project Name:** SmartCampus

**Description:**
SmartCampus is a Django-based web application designed to manage core college campus operations including student management, attendance tracking (including QR-based scanning), library checkouts, mess payment tracking, exam/results management, fee collection, hostel management (complaints and leave applications), and administrative dashboards.

**Primary Users:**
- **Students**: Manage their profile, view attendance, results, ID cards, and use QR scan features.
- **Faculty / Staff**: Manage courses/subjects, enter results, view attendance reports.
- **Administrators (Master Admin)**: Oversee students, faculty, payments, mess transactions, and complaints.


## 2. Goals

- Provide a unified portal for student and administrative campus workflows.
- Reduce manual paperwork by offering QR-based attendance and library/mess scanning.
- Offer transparency into fees, payments, and academic records.
- Enable basic hostel facility management (complaints, leave applications, room allocation).


## 3. Scope & Features

### 3.1 Authentication & Authorization
- User login/logout (Django `auth` system).
- User registration (basic signup form).
- Staff-only access for result entry.
- Master admin dashboard for privileged users.

### 3.2 Student Management
- Add / edit / delete student records.
- Generate and store per-student QR code (based on roll number).
- Display student profile including attendance statistics and pending library books.
- Generate student ID card (single & bulk views).

### 3.3 Faculty & Courses
- Add / edit / delete faculty records (name, department, subject, email).
- Add / edit / delete courses (course name, course code, linked faculty).
- Add subjects for courses (subject name, code, credit hours).

### 3.4 Attendance Management
- Manual attendance entry per student + course + date + status (Present/Absent/Late).
- QR scanner endpoint for marking attendance by scanning student roll number.
- Prevent duplicate attendance for same student+date.
- View attendance reports (all attendance records).
- Optional email alert when a student is marked absent (SMTP integration).

### 3.5 Library / Book Issuance
- Issue books to students via QR scan input + book title.
- Store book issue history (issue date, return date, returned flag).
- API endpoint for issuing books via POST (possibly for external scanner clients).

### 3.6 Mess Wallet & Payments
- Student mess wallet with balance and transaction history.
- QR-based mess payment endpoint that deducts preset meal cost and logs transactions.
- Auto-recharge logic when balance is low (hardcoded top-up amount).
- Master admin/dashboards show mess transaction history.

### 3.7 Fee Management
- Record fee payments with generated receipt numbers.
- Support multiple fee types (Tuition, Exam, Hostel, Library).
- Dashboard to view fee collection totals and daily collections.
- Ability to view receipt format for an individual payment.

### 3.8 Exam & Results
- Manage exam schedules (course, subject, date, time, room).
- Students can view results by roll number.
- Staff can add results via a form (multiple subjects per submission).
- GPA calculation based on marks and total marks.

### 3.9 Hostel Management
- Hostels have rooms assigned using `HostelRoom` model.
- Students can submit complaints (category + description).
- Apply for leave (start/end date + reason) (primarily stored/logged).
- Dashboard shows mess menu, room info, and user complaints.

### 3.10 Notices
- Create and store notices (title, content, created date).
- Display notices in UI (likely on home page or dedicated view).


## 4. User Stories

1. **As a student**, I want to log in and view my attendance, so I can know if I’ve been marked present.
2. **As a student**, I want to scan my ID QR to mark attendance quickly.
3. **As a faculty member**, I want to add exam results for students so they can view them online.
4. **As an admin**, I want to view and manage all student/faculty records.
5. **As a mess operator**, I want to deduct meal charges from a student’s wallet via QR scan.
6. **As a librarian**, I want to issue books and track due dates.
7. **As a hostel resident**, I want to submit complaints and apply for leave.


## 5. Functional Requirements

### 5.1 Core Data Models (as implemented)
- `Student` (name, roll_no, course, photo, qr_code)
- `Faculty` (name, department, subject, email)
- `Course` (course_name, course_code, faculty)
- `Attendance` (student, course, date, status, is_present)
- `Notice` (title, content, created_at)
- `Book` (title, book_id, author, is_issued, issued_to)
- `BookIssue` (student, book_name, issue_date, return_date, is_returned)
- `MessWallet` (student, balance, last_transaction)
- `MessTransaction` (student, amount, date, meal_type)
- `ExamSchedule` (course, subject_name, exam_date, exam_time, room_no)
- `Result` (student, subject, marks_obtained, total_marks, semester)
- `FeePayment` (student, receipt_no, amount, fee_type, date_paid, status)
- `MessMenu` (day, breakfast, lunch, dinner)
- `HostelRoom` (student (User), room_number, block)
- `Complaint` (user, category, description, is_resolved, created_at)
- `LeaveApplication` (user, start_date, end_date, reason, created_at)
- `Payment` (student (User), txn_id, amount, status, date)
- `Subject` (course, subject_name, subject_code, credit_hours)
- `FeeTransaction` (student, receipt_no, category, amount, date, status)

### 5.2 Key Pages / Views
- `/login` - Login page
- `/register` - Sign-up
- `/home` - Dashboard summary (counts, recent transactions)
- `/master_admin` - Administrative dashboard
- `/students` - Student list
- `/add_student`, `/edit_student/{id}`, `/delete_student/{id}`
- `/faculty`, `/add_faculty`, `/edit_faculty/{id}`, `/delete_faculty/{id}`
- `/courses`, `/add_course`, `/update_course/{id}`, `/delete_course/{id}`
- `/add_subject/{course_id}`
- `/mark_attendance` - Attendance entry with QR support
- `/qr_scanner` - QR attendance scanner
- `/view_attendance` - Attendance report
- `/library_scanner` - Book issue flow + history
- `/mess_scanner` - Mess payment scanner
- `/fees_dashboard`, `/collect_fee`, `/view_receipt/{receipt_no}`
- `/exam_portal` - View exams/results
- `/result_page`, `/add_result_form` - Result viewing and entry
- `/hostel_page` - Hostel dashboard, including menu, room, complaints
- `/apply_leave`, `/submit_complaint` - Hostel workflows
- `/student_profile` - Profile + attendance/book status


## 6. Non-functional Requirements

### 6.1 Performance
- Pages should load within a few seconds on modest hardware.
- QR scans and API actions should respond quickly (sub-second for network calls).

### 6.2 Security
- Use Django auth for user management.
- Restrict result entry and admin views to staff users.
- Validate all user inputs, especially roll numbers and IDs.
- Secure media uploads (student photos, QR codes).

### 6.3 Maintainability
- Keep models normalized (avoid duplication) and clean up redundant model definitions.
- Separate business logic from views (move heavy logic to services in future).
- Use consistent naming and avoid repeating imports.

### 6.4 Scalability
- Designed for a small to medium campus.
- Use SQLite as default DB; consider migrating to PostgreSQL for production.


## 7. Dependencies

- Django (web framework)
- Pillow (image handling for QR code generation)
- qrcode (QR code generation)
- sqlite3 (default DB)


## 8. Deployment

### 8.1 Development Setup
1. Create virtualenv
2. Install requirements (likely `django`, `qrcode`, `Pillow`)
3. Run migrations (`python manage.py migrate`)
4. Create superuser (`python manage.py createsuperuser`)
5. Run server (`python manage.py runserver`)

### 8.2 Production
- Use proper WSGI/ASGI hosting (Gunicorn + Nginx).
- Use a production database (PostgreSQL/MySQL).
- Configure static/media file serving.
- Secure SMTP credentials and remove hardcoded email passwords.


## 9. Known Issues & Technical Debt

- `models.py` contains duplicate model definitions (e.g., `Result` twice) and repeated imports.
- `views.py` contains duplicate function definitions and commented-out fixes; needs refactor.
- Hardcoded email credentials and plaintext SMTP password in code.
- Some view functions use `request.POST.get('student_id')` but then fetch by `roll_no`.
- Attendance model uses `unique_together` on (`student`, `date`) but not on (`course`, `date`), may allow duplicate attendance per course.
- `HostelRoom` links to `User` rather than `Student`, creating mixed user representation.


## 10. Future Enhancements

- Add role-based access control (Admin / Faculty / Student)
- Add API endpoints (REST) for mobile apps.
- Add reporting dashboards (attendance trends, fee reports).
- Add notification system (email/SMS) for absence alerts, due fees.
- Improve UI/UX, mobile responsive design.
- Add automated tests (unit + integration).


---

> NOTE: This PRD is based on current codebase structure and inferred application behavior. As the project evolves, the PRD should be updated to reflect new features, architectural changes, and clarified user flows.
