import decimal
from urllib import request
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages
from .models import (
    ExamSchedule, HostelRoom, LeaveApplication, MessMenu, 
    MessTransaction, MessWallet, Result, Student, 
    Faculty, Course, Attendance, Complaint, BookIssue, FeePayment, Subject
)
from django.http import JsonResponse # Ye zaroori hai result bhejne ke liye
import datetime  # Ye miss hone par 500 error aata hai
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from .models import Student, Attendance  # Models check karo
from django.db.models import Count
from django.contrib.auth.decorators import login_required
from .models import Complaint

def home(request):
    # Sabhi transactions ko mangwao (naya upar rahega)
    history = MessTransaction.objects.all().order_by('-date')[:5] 
    
    # Ye context hi data ko HTML tak le jata hai
    context = {
        'student_count': Student.objects.count(),
        'faculty_count': Faculty.objects.count(),
        'course_count': Course.objects.count(),
        'history': history, # YE LINE ZAROORI HAI
    }
    return render(request, 'index.html', context)

def _is_faculty(user):
    """Return True if the user has a linked Faculty profile or is a Django superuser."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    return Faculty.objects.filter(user=user).exists()


def _is_student(user):
    """Return True if the user has a linked Student profile."""
    if not user or not user.is_authenticated:
        return False
    return Student.objects.filter(user=user).exists()


def login_view(request):
    """Main login for both students and faculty."""
    if request.user.is_authenticated:
        if _is_faculty(request.user):
            return redirect('master_admin')
        return redirect('home')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is not None:
            login(request, user)
            messages.success(request, f"Welcome, {user.first_name if user.first_name else username_input}!")

            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)

            if _is_faculty(user):
                return redirect('master_admin')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password. Please try again.')

    return render(request, 'login.html')


def admin_login_view(request):
    """Dedicated admin portal login — faculty accounts only."""
    if request.user.is_authenticated and _is_faculty(request.user):
        return redirect('master_admin')

    if request.method == 'POST':
        username_input = request.POST.get('username')
        password_input = request.POST.get('password')

        user = authenticate(request, username=username_input, password=password_input)

        if user is None:
            messages.error(request, "Invalid username or password. Please try again.")
        elif not _is_faculty(user):
            messages.error(request, "Access denied. The admin portal is restricted to faculty accounts only.")
        else:
            login(request, user)
            messages.success(request, f"Welcome back, {user.first_name or user.username}.")
            next_url = request.GET.get('next')
            return redirect(next_url) if next_url else redirect('master_admin')

    return render(request, 'admin_login.html')

from django.db.models import Sum, Count, Q 
from .models import Student, Faculty, Course, MessTransaction, Complaint, Payment, MessMenu, LeaveApplication, Attendance, Notice 

def master_admin(request):
    # Faculty-only gate: bounce everyone else to the admin login page
    if not _is_faculty(request.user):
        return redirect('admin_login')

    # --- NEW: Mess Menu Save/Update Logic ---
    if request.method == "POST" and 'update_mess' in request.POST:
        day = request.POST.get('day')
        breakfast = request.POST.get('breakfast')
        lunch = request.POST.get('lunch')
        dinner = request.POST.get('dinner')

        try:
            # update_or_create use kiya hai taaki ek din ki do entry na ho
            MessMenu.objects.update_or_create(
                day=day, 
                defaults={
                    'breakfast': breakfast,
                    'lunch': lunch,
                    'dinner': dinner
                }
            )
            messages.success(request, f"Mess menu for {day} updated successfully.")
        except Exception as e:
            messages.error(request, f"Failed to update mess menu: {e}")
        return redirect('master_admin')

    # --- STEP 4: Notice Posting Logic ---
    if request.method == "POST" and 'post_notice' in request.POST:
        title = request.POST.get('title')
        message = request.POST.get('message')
        urgent = request.POST.get('is_urgent') == 'on'
        
        try:
            Notice.objects.create(title=title, message=message, is_urgent=urgent)
            messages.success(request, "Notice broadcast successfully.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")
        return redirect('master_admin')

    # --- Basic Data Fetching ---
    students = Student.objects.all().order_by('-id')
    faculties = Faculty.objects.all().order_by('-id')
    courses = Course.objects.all()

    # --- Mess Menu & Leave Requests ---
    all_leaves = LeaveApplication.objects.all().order_by('-created_at')
    current_mess_menu = MessMenu.objects.all()

    # --- STEP 1: Smart Attendance Report Logic ---
    total_working_days = Attendance.objects.values('date').distinct().count() or 1
    
    low_attendance_list = []
    all_students_with_attendance = Student.objects.annotate(
        present_days=Count('attendance', filter=Q(attendance__status='Present'))
    )

    for s in all_students_with_attendance:
        attendance_percent = (s.present_days / total_working_days) * 100
        if attendance_percent < 75:
            s.attendance_perc = round(attendance_percent, 1)
            low_attendance_list.append(s)

    # --- Finance & Fees Logic ---
    recent_transactions = []
    total_collected = 0
    try:
        all_transactions = Payment.objects.all().order_by('-id')
        recent_transactions = all_transactions[:5] 
        total_collected = all_transactions.aggregate(Sum('amount'))['amount__sum'] or 0
    except Exception as e:
        print(f"Finance Error: {e}")

    # --- Mess Transactions, Complaints & Notices ---
    complaints = Complaint.objects.all().order_by('-id')
    notices = Notice.objects.all().order_by('-date_posted')[:5]

    # --- Context Update ---
    context = {
        'students': students,
        'faculties': faculties,
        'courses': courses,
        'recent_transactions': recent_transactions,
        'complaints': complaints,
        'all_leaves': all_leaves,
        'current_mess_menu': current_mess_menu,
        'notices': notices,
        'low_attendance_list': low_attendance_list,
        'total_students': students.count(),
        'total_faculty': faculties.count(),
        'total_courses': courses.count(),
        'total_collected': total_collected,
        'pending_complaints': complaints.count(),
        'pending_leaves': all_leaves.filter(status='Pending').count(),
        'short_attendance_count': len(low_attendance_list),
    }

    return render(request, 'master_admin.html', context)

# Student Delete karne ka function (ise bhi update kar lo)
def delete_student(request, student_id):
    student = get_object_or_404(Student, id=student_id)
    name = student.name
    student.delete()
    messages.success(request, f"{name}'s record has been deleted successfully.")
    return redirect('master_admin')

# Self-registration is disabled on the public/user side.
# Students can only be created by an administrator via the admin's Add Student page.
def register_view(request):
    messages.info(request, "Self-registration is disabled. Please contact your administrator to create an account.")
    return redirect('login')

# Logout
def logout_view(request):
    logout(request)
    return redirect('login')

# 1. Add Student (admin-side) — optionally creates a linked login account
def add_student(request):
    courses = Course.objects.all().order_by('course_name')

    if request.method == 'POST':
        name_data = (request.POST.get('name') or '').strip()
        roll_data = (request.POST.get('roll_no') or '').strip()
        course_data = (request.POST.get('course') or '').strip()
        email_data = (request.POST.get('email') or '').strip()
        phone_data = (request.POST.get('phone') or '').strip()
        photo_file = request.FILES.get('photo')

        create_account = request.POST.get('create_account') == 'on'
        username_data = (request.POST.get('username') or '').strip()
        password_data = request.POST.get('password') or ''

        if not name_data or not roll_data:
            messages.error(request, 'Name and Roll Number are required.')
            return render(request, 'add_student.html', {'courses': courses})

        if Student.objects.filter(roll_no=roll_data).exists():
            messages.error(request, f'Error: Roll No {roll_data} already exists in the database.')
            return render(request, 'add_student.html', {'courses': courses})

        user_obj = None
        if create_account:
            if not username_data or not password_data:
                messages.error(request, 'Username and password are required when creating a login account.')
                return render(request, 'add_student.html', {'courses': courses})
            if User.objects.filter(username=username_data).exists():
                messages.error(request, f"Username '{username_data}' is already taken.")
                return render(request, 'add_student.html', {'courses': courses})
            user_obj = User.objects.create_user(
                username=username_data,
                email=email_data,
                password=password_data,
                first_name=name_data.split(' ', 1)[0],
                last_name=name_data.split(' ', 1)[1] if ' ' in name_data else '',
            )

        Student.objects.create(
            user=user_obj,
            name=name_data,
            roll_no=roll_data,
            course=course_data or None,
            email=email_data or None,
            phone=phone_data or None,
            photo=photo_file,
        )
        messages.success(request, f"Student '{name_data}' added successfully.")
        return redirect('students_page')

    return render(request, 'add_student.html', {'courses': courses})

# 2. Student List Page (Isme data fetch ho raha hai)
def students_page(request):
    # Database se saare students mangwao
    all_students = Student.objects.all() 
    
    # Is 'all_students' ko 'students' naam se HTML ko bhejo
    return render(request, 'students.html', {'students': all_students})

def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.delete()
    return redirect('students_page')


def edit_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    courses = Course.objects.all().order_by('course_name')

    if request.method == "POST":
        name = (request.POST.get('name') or '').strip()
        roll_no = (request.POST.get('roll_no') or '').strip()
        course = (request.POST.get('course') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        photo_file = request.FILES.get('photo')

        if not name or not roll_no:
            messages.error(request, 'Name and Roll Number are required.')
            return render(request, 'edit_student.html', {'student': student, 'courses': courses})

        # Duplicate roll_no check (exclude current student)
        if Student.objects.filter(roll_no=roll_no).exclude(pk=student.pk).exists():
            messages.error(request, f'Roll No {roll_no} is already assigned to another student.')
            return render(request, 'edit_student.html', {'student': student, 'courses': courses})

        student.name = name
        student.roll_no = roll_no
        student.course = course or None
        student.email = email or None
        student.phone = phone or None
        if photo_file:
            student.photo = photo_file
        student.save()

        messages.success(request, f"Student '{name}' updated successfully.")
        return redirect('students_page')

    return render(request, 'edit_student.html', {'student': student, 'courses': courses})

import smtplib
from email.mime.text import MIMEText
from .models import Student, Course, Attendance

def mark_attendance(request):
    """
    Course-wise bulk attendance marking.

    Flow:
      GET ?course=<id>&date=<YYYY-MM-DD>   -> show all students of that course
                                              with Present/Absent/Late radios
      POST (course + date + status_<student_id> per student) -> save all at once
    """
    courses = Course.objects.all().order_by('course_name')
    today = datetime.date.today().isoformat()

    # ---------- POST: bulk save ----------
    if request.method == 'POST':
        course_id = request.POST.get('course')
        date_str = request.POST.get('date') or today
        try:
            attendance_date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            attendance_date = datetime.date.today()
        course_obj = get_object_or_404(Course, id=course_id)

        saved = 0
        skipped = 0
        for key, value in request.POST.items():
            if not key.startswith('status_'):
                continue
            try:
                student_id = int(key.split('_', 1)[1])
            except (ValueError, IndexError):
                continue

            student_obj = Student.objects.filter(id=student_id).first()
            if not student_obj:
                continue

            # Prevent duplicates for same student + date
            if Attendance.objects.filter(student=student_obj, date=attendance_date).exists():
                skipped += 1
                continue

            Attendance.objects.create(
                student=student_obj,
                course=course_obj,
                status=value,
                date=attendance_date,
                is_present=(value == 'Present'),
            )
            saved += 1

        if saved:
            messages.success(
                request,
                f"Attendance saved for {saved} student(s) in {course_obj.course_name}."
            )
        if skipped:
            messages.warning(
                request,
                f"{skipped} record(s) were skipped because attendance was already marked for that date."
            )
        if not saved and not skipped:
            messages.error(request, "No students were marked. Please check the form.")

        return redirect(f"{request.path}?course={course_id}&date={attendance_date}")

    # ---------- GET: show selector + (optional) student list ----------
    selected_course_id = request.GET.get('course')
    selected_date = request.GET.get('date') or today
    selected_course = None
    course_students = []

    if selected_course_id:
        selected_course = Course.objects.filter(id=selected_course_id).first()
        if selected_course:
            # Filter students whose 'course' field matches this course.
            # Student.course is a free CharField like "B.COM/Business Communication",
            # so match on startswith/icontains of the selected course name.
            from django.db.models import Q
            name = selected_course.course_name
            course_students = list(
                Student.objects.filter(
                    Q(course__istartswith=name) | Q(course__iexact=name)
                ).order_by('roll_no')
            )

            # Mark students who already have attendance for this date so the
            # template can disable their row.
            marked_ids = set(
                Attendance.objects.filter(
                    student__in=course_students, date=selected_date
                ).values_list('student_id', flat=True)
            )
            for s in course_students:
                s.already_marked = s.id in marked_ids

    # Recent history (last 30 records)
    attendance_list = Attendance.objects.all().order_by('-date', '-id')[:30]

    context = {
        'courses': courses,
        'selected_course': selected_course,
        'selected_course_id': selected_course_id,
        'selected_date': selected_date,
        'today': today,
        'course_students': course_students,
        'attendance_list': attendance_list,
    }
    return render(request, 'mark_attendance.html', context)

from .models import Faculty, Course

# Faculty List View
def faculty_page(request):
    faculties = Faculty.objects.all()
    return render(request, 'faculty.html', {'faculties': faculties})

from .models import Course, Faculty
# 1. Sabhi Degrees Dekhne Ke Liye
def courses_page(request):
    courses = Course.objects.all()
    # Tumne file ka naam badla tha, wahi yahan use ho raha hai
    return render(request, 'course_catalog.html', {'courses': courses})

from django.db import IntegrityError # Ye import zaroori hai
def add_course(request):
    faculties = Faculty.objects.all()
    if request.method == 'POST':
        name = request.POST.get('course_name')
        code = request.POST.get('course_code')
        faculty_id = request.POST.get('faculty')
        
        faculty_obj = None
        if faculty_id:
            faculty_obj = get_object_or_404(Faculty, id=faculty_id)
        
        try:
            Course.objects.create(
                course_name=name,
                course_code=code, 
                faculty=faculty_obj
            )
            messages.success(request, f"{name} added successfully.")
            return redirect('courses_page')
        except IntegrityError:
            # Agar duplicate code aaya toh ye error dikhayega
            messages.error(request, f"The code '{code}' is already assigned to another course. Please use a different code.")
            
    return render(request, 'add_course.html', {'faculties': faculties})

# 3. Degree Update Karne Ke Liye (Fixed Version)
def update_course(request, pk):
    course = get_object_or_404(Course, id=pk)
    faculties = Faculty.objects.all()
    
    if request.method == 'POST':
        course.course_name = request.POST.get('course_name')
        # FIX: Yahan bhi 'course_id' ko 'course_code' kar do
        course.course_code = request.POST.get('course_code')
        faculty_id = request.POST.get('faculty')
        
        if faculty_id:
            course.faculty = Faculty.objects.get(id=faculty_id)
            
        course.save()
        messages.success(request, "Degree Updated!")
        return redirect('courses_page')
    
    return render(request, 'add_course.html', {'course': course, 'faculties': faculties})

# 4. Degree Delete Karne Ke Liye
def delete_course(request, pk):
    course = get_object_or_404(Course, id=pk)
    course.delete()
    messages.success(request, "Degree Deleted!")
    return redirect('courses_page')

def view_attendance(request):
    # Sabhi attendance records mangwao
    from .models import Attendance
    data = Attendance.objects.all().order_by('-date')
    return render(request, 'view_attendance.html', {'records': data})

def settings_page(request):
    return render(request, 'settings.html')

def add_faculty(request):
    if request.method != 'POST':
        return redirect('faculty_page')

    from django.contrib.auth.models import Group

    name = (request.POST.get('name') or '').strip()
    department = (request.POST.get('department') or 'General').strip()
    subject = (request.POST.get('subject') or '').strip()
    email = (request.POST.get('email') or '').strip()
    phone = (request.POST.get('phone') or '').strip()
    username = (request.POST.get('username') or '').strip()
    password = request.POST.get('password') or ''
    confirm_password = request.POST.get('confirm_password') or ''

    # Validation
    if not all([name, subject, email, username, password]):
        messages.error(request, 'Please fill in all required fields (name, subject, email, username, password).')
        return redirect('faculty_page')

    if password != confirm_password:
        messages.error(request, 'Passwords do not match.')
        return redirect('faculty_page')

    if Faculty.objects.filter(email=email).exists():
        messages.error(request, f'A faculty member with email {email} already exists.')
        return redirect('faculty_page')

    if User.objects.filter(username=username).exists():
        messages.error(request, f"Username '{username}' is already taken.")
        return redirect('faculty_page')

    # Create the login account
    name_parts = name.split(' ', 1)
    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=name_parts[0],
        last_name=name_parts[1] if len(name_parts) > 1 else '',
    )
    user.is_staff = True
    user.save()

    # Put them in the Faculty group
    faculty_group, _ = Group.objects.get_or_create(name='Faculty')
    user.groups.add(faculty_group)

    # Create the Faculty profile
    Faculty.objects.create(
        user=user,
        name=name,
        department=department,
        subject=subject,
        email=email,
        phone=phone or None,
    )

    messages.success(request, f'Faculty {name} added successfully. They can now log in at the admin portal.')
    return redirect('faculty_page')

# Delete karne ke liye
def delete_faculty(request, id):
    faculty = get_object_or_404(Faculty, id=id)
    faculty.delete()
    return redirect('faculty_page') # Wapas list par bhej dega

def edit_faculty(request, id):
    faculty = get_object_or_404(Faculty, id=id)

    if request.method == "POST":
        name = (request.POST.get('name') or '').strip()
        department = (request.POST.get('department') or 'General').strip()
        subject = (request.POST.get('subject') or '').strip()
        email = (request.POST.get('email') or '').strip()
        phone = (request.POST.get('phone') or '').strip()
        username = (request.POST.get('username') or '').strip()
        password = request.POST.get('password') or ''
        confirm_password = request.POST.get('confirm_password') or ''

        # Validation
        if not all([name, subject, email]):
            messages.error(request, 'Name, subject and email are required.')
            return render(request, 'edit_faculty.html', {'f': faculty})

        # Email uniqueness (exclude self)
        if Faculty.objects.filter(email=email).exclude(pk=faculty.pk).exists():
            messages.error(request, f'Another faculty member already uses the email {email}.')
            return render(request, 'edit_faculty.html', {'f': faculty})

        # Password match check (only if they're trying to change it)
        if password or confirm_password:
            if password != confirm_password:
                messages.error(request, 'Passwords do not match.')
                return render(request, 'edit_faculty.html', {'f': faculty})

        # Username uniqueness (exclude self's user)
        if username and faculty.user:
            qs = User.objects.filter(username=username).exclude(pk=faculty.user.pk)
            if qs.exists():
                messages.error(request, f"Username '{username}' is already taken.")
                return render(request, 'edit_faculty.html', {'f': faculty})

        # Update faculty fields
        faculty.name = name
        faculty.department = department
        faculty.subject = subject
        faculty.email = email
        faculty.phone = phone or None
        faculty.save()

        # Update linked user (if exists)
        if faculty.user:
            user = faculty.user
            if username:
                user.username = username
            user.email = email
            name_parts = name.split(' ', 1)
            user.first_name = name_parts[0]
            user.last_name = name_parts[1] if len(name_parts) > 1 else ''
            if password:
                user.set_password(password)
            user.save()

        messages.success(request, f"{name}'s profile updated successfully.")
        return redirect('faculty_page')

    return render(request, 'edit_faculty.html', {'f': faculty})

import datetime
from django.http import JsonResponse
from .models import Student, Attendance, Course

# DHAYAN DE: Maine yahan naam badal kar 'qr_scanner_view' kar diya hai
def qr_scanner_view(request):
    if request.method == "POST":
        scanned_roll_no = request.POST.get('roll_no')
        
        try:
            # 1. Student ko dhundho
            student = Student.objects.get(roll_no=scanned_roll_no)
            
            # 2. Student kis course mein hai, wo pata karo
            today = datetime.date.today()
            
            # 3. Attendance lagao
            # Note: defaults mein wahi fields rakho jo Attendance model mein hain
            obj, created = Attendance.objects.get_or_create(
                student=student,
                date=today,
                defaults={
                    'status': 'Present',
                    # Agar model mein 'course' field hai toh student ka course pass karo
                    'course': getattr(student, 'course', None) 
                }
            )

            if not created:
                return JsonResponse({'status': 'info', 'message': f'Attendance for {student.name} has already been marked.'})

            return JsonResponse({'status': 'success', 'message': f'{student.name} marked Present'})

        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Roll No not found in the database.'}, status=404)
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)}, status=500)
    
    # Template ka path check kar lena: agar folder ke andar hai toh 'campus/qr_scanner.html'
    return render(request, 'qr_scanner.html')

from .models import Student  # Ensure your model name is correct
def student_id_card_view(request, pk=None):
    # Agar pk (id) mil raha hai toh us student ka data nikalo
    if pk:
        student = get_object_or_404(Student, pk=pk)
    else:
        # Agar pk nahi hai toh logged-in student ka data nikalo (default behavior)
        student = get_object_or_404(Student, user=request.user)
    
    return render(request, 'student_id_card.html', {'student': student})
def all_id_cards(request):
    from .models import Student
    students = Student.objects.all()
    return render(request, 'all_id_cards.html', {'students': students})


from django.http import JsonResponse
from .models import Student, Book
from django.views.decorators.csrf import csrf_exempt

from .models import Student, BookIssue
from django.contrib import messages

def library_scanner(request):
    if request.method == "POST":
        scanned_data = request.POST.get('qr_data')
        book_title = request.POST.get('book_name')

        print(f"--- DEBUG START ---")
        print(f"Scanned Roll No: {scanned_data}")
        print(f"Book Title: {book_title}")

        if not scanned_data or not book_title:
            messages.error(request, "Both fields are required.")
            return redirect('library_scanner')

        try:
            # Yahan hum dhoond rahe hain
            student = Student.objects.get(roll_no=scanned_data)
            BookIssue.objects.create(student=student, book_name=book_title)
            messages.success(request, f"Done! {book_title} issued to {student.name}")
        except Student.DoesNotExist:
            print(f"ERROR: Student with roll {scanned_data} not found in DB")
            messages.error(request, f"Roll No {scanned_data} not found in the database.")
        except Exception as e:
            print(f"ERROR: {e}")
            messages.error(request, f"Something went wrong: {e}")

        return redirect('library_scanner')

    history = BookIssue.objects.all().order_by('-issue_date')[:10]
    return render(request, 'library_scanner.html', {'history': history})

@csrf_exempt
def issue_book_api(request):
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        book_id = request.POST.get('book_id') # Agar book ka bhi QR hai toh
        
        try:
            student = Student.objects.get(roll_no=student_id)
            # Yahan aap apni Library model mein entry save kar sakte ho
            # Example: LibraryLog.objects.create(student=student, book_name="Python Pro", issue_date=timezone.now())
            
            return JsonResponse({'status': 'success', 'message': f'Book issued to {student.name}'})
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Student not found!'})
        
# 1. Scanner Page kholne ke liye (Niche history dikhayega)
def mess_scanner(request):
    # Sabse latest 5 transactions ko history mein bhejenge
    recent_history = MessTransaction.objects.all().order_by('-date')[:5]
    return render(request, 'mess_scanner.html', {'history': recent_history})

# 2. QR Scan hone par paise kaatne ke liye
@csrf_exempt
def mess_payment_api(request):
    if request.method == "POST":
        student_id = request.POST.get('student_id')
        meal_cost = decimal.Decimal('50.00')
        
        try:
            student = Student.objects.get(roll_no=student_id)
            
            # Wallet check ya create (500 balance default)
            wallet, created = MessWallet.objects.get_or_create(
                student=student,
                defaults={'balance': decimal.Decimal('500.00')}
            )

            # Auto-Recharge (Testing ke liye)
            if wallet.balance < meal_cost:
                wallet.balance += decimal.Decimal('500.00')
                wallet.save()

            # Paisa Kaato
            wallet.balance -= meal_cost
            wallet.save()
            
            # Ye line history mein record save karti hai
            MessTransaction.objects.create(
                student=student, 
                amount=meal_cost, 
                meal_type="Lunch"
            )
            
            return JsonResponse({
                'status': 'success', 
                'balance': str(wallet.balance),
                'student_name': student.name
            })
            
        except Student.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'ID not found!'})
    return JsonResponse({'status': 'error', 'message': 'Invalid Request'})

from .models import Student, Attendance, BookIssue
def student_profile_view(request):
    roll_no = request.GET.get('roll_no')
    student = None
    attendance_count = 0
    pending_books = None

    if roll_no:
        # Roll No se student dhoondho
        student = Student.objects.filter(roll_no=roll_no).first()
        if student:
            # Kitne din Present raha
            attendance_count = Attendance.objects.filter(student=student, status='Present').count()
            # Kaunsi books pending hain
            pending_books = BookIssue.objects.filter(student=student, is_returned=False)
        else:
            messages.error(request, "This roll number is not in the records.")

    return render(request, 'student_profile.html', {
        'student': student,
        'attendance_count': attendance_count,
        'pending_books': pending_books
    })

from django.shortcuts import render
from .models import Student, Result, ExamSchedule
from django.db.models import Q

def exam_portal_view(request):
    roll_no = request.GET.get('roll_no')
    student = None
    results = None
    exams = None

    if roll_no:
        # 1. Student ko dhoondo
        student = Student.objects.filter(roll_no=roll_no).first()
        
        if student:
            # 2. Results fetch karo
            results = Result.objects.filter(student=student)
            
            # 3. FINAL FIX: Hum student ke course ko string bana kar search karenge
            # Taaki ID wala 'ValueError' kabhi na aaye
            course_name_str = str(student.course)

            # Hum multiple tareeqon se dhoondenge taaki error na aaye
            try:
                # Sabse pehle check karo agar 'course' field ek string match kar sake
                # Hum '__course_name' ya direct 'course' par lookup karenge jo FieldError nahi dega
                exams = ExamSchedule.objects.filter(
                    Q(course__course_name__icontains=course_name_str) | 
                    Q(course__icontains=course_name_str)
                ).distinct().order_by('exam_date')
            except Exception:
                # Agar upar wala fail ho jaye (ForeignKey issues), toh ye fallback use karo
                # Isme hum poore queryset se python level par filter kar lenge (Slow but 100% Safe)
                all_exams = ExamSchedule.objects.all()
                exams = [e for e in all_exams if str(e.course).lower() == course_name_str.lower()]

    return render(request, 'exam_portal.html', {
        'student': student,
        'results': results,
        'exams': exams
    })

from django.db.models import Sum
from .models import FeePayment
def fees_dashboard(request):
    # Saari payments nikalne ke liye
    history = FeePayment.objects.all().order_by('-date_paid')
    
    # Total Calculation
    total_collected = FeePayment.objects.aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Aaj ki collection
    import datetime
    today = datetime.date.today()
    today_collection = FeePayment.objects.filter(date_paid=today).aggregate(Sum('amount'))['amount__sum'] or 0

    context = {
        'history': history,
        'total_collected': total_collected,
        'today_collection': today_collection,
    }
    return render(request, 'fees_dashboard.html', context)

def collect_fee(request):
    if request.method == "POST":
        # Form se jo ID aa rahi hai
        input_id = request.POST.get('student_id') 
        amount = request.POST.get('amount')
        fee_type = request.POST.get('fee_type')

        try:
            # DHAR RAKHO: Yahan 'student_id' ki jagah 'roll_no' use karo
            student = Student.objects.get(roll_no=input_id)
            
            FeePayment.objects.create(
                student=student,
                amount=amount,
                fee_type=fee_type,
                status='Paid'
            )
            # Success message (optional)
            return redirect('fees_dashboard')
            
        except Student.DoesNotExist:
            # Agar student nahi mila toh
            return HttpResponse("Invalid roll number — not found in the database.")

    return redirect('fees_dashboard')

def view_receipt(request, receipt_no):
    # Receipt number se payment dhoondo
    payment = get_object_or_404(FeePayment, receipt_no=receipt_no)
    
    context = {
        'payment': payment,
    }
    return render(request, 'receipt_format.html', context)

@login_required 
def hostel_dashboard(request):
    # 1. Database se saara mess menu uthao
    menu = MessMenu.objects.all() 
    
    # 2. Login student ka room dhoondo
    room = HostelRoom.objects.filter(student=request.user).first() 
    
    # 3. YAHAN FIX KARNA HAI: 'student' ki jagah 'user' likho
    complaints = Complaint.objects.filter(user=request.user).order_by('-created_at')

    context = {
        'menu': menu,
        'room': room,
        'complaints': complaints,
    }
    
    return render(request, 'hostel_page.html', context)

def apply_leave(request):
    if request.method == 'POST':
        # Yahan aapka form data aa raha hai
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        reason = request.POST.get('reason')
        
        # Abhi ke liye sirf console par print karte hain aur message dikhate hain
        print(f"Leave Applied: {start_date} to {end_date}")
        
        messages.success(request, "Leave application submitted successfully.")
        return redirect('hostel_page') # Wapas dashboard bhej do
    return redirect('hostel_page')

from django.contrib.auth.decorators import login_required
from .models import Complaint, LeaveApplication, MessMenu, HostelRoom
def submit_complaint(request):
    if request.method == 'POST':
        cat = request.POST.get('category')
        desc = request.POST.get('description')
        
        # Make sure user is logged in before saving
        if request.user.is_authenticated:
            Complaint.objects.create(
                user=request.user, 
                category=cat, 
                description=desc
            )
            messages.success(request, "Complaint registered successfully!")
            return redirect('hostel_page') # Yahan error aa rahi thi
        else:
            messages.error(request, "Please log in first.")
            return redirect('login') 

    # Agar GET request hai ya post fail ho gaya
    return redirect('hostel_page')
    
from .models import Payment  # Payment model ko import karna mat bhulna
def submit_payment_ref(request):
    if request.method == "POST":
        txn_id = request.POST.get('txn_id')
        Payment.objects.create(
            student=request.user,
            txn_id=txn_id,
            amount=1200,
            status='Pending'
        )
        messages.success(request, f"Payment ID {txn_id} submitted successfully.")
        
        # Ye line change kar di hai, ab error nahi aayegi
        return redirect(request.META.get('HTTP_REFERER', '/')) 
    
    return redirect('/')

from .models import Student, Result  # Make sure models are imported
# --- 1. VIEW RESULT LOGIC ---
def view_result(request):
    student = None
    results = None
    gpa = 0
    
    if request.method == "POST":
        roll_no = request.POST.get('roll_no')
        # Roll number se student dhundna
        try:
            student = Student.objects.get(roll_no=roll_no)
            results = Result.objects.filter(student=student)
            
            # Chota sa logic GPA nikalne ke liye
            if results:
                total_obtained = sum(r.obtained_marks for r in results)
                total_subjects = results.count()
                # Assuming 100 marks per subject for GPA 10 scale
                gpa = (total_obtained / (total_subjects * 100)) * 10
        except Student.DoesNotExist:
            messages.error(request, "This roll number is not in the database.")
            student = None

    return render(request, 'result_page.html', {
        'student': student, 
        'results': results,
        'gpa': round(gpa, 2)
    })

# --- 2. ADD RESULT FROM WEB (FRONTEND ENTRY) ---
def add_result_web(request):
    # Security: Sirf Staff/Teacher hi result daal sake
    if not request.user.is_staff:
        messages.error(request, "You do not have access to this page.")
        return redirect('home')

    students = Student.objects.all() # Dropdown ke liye
    
    if request.method == "POST":
        student_id = request.POST.get('student')
        sem = request.POST.get('semester')
        
        # Multiple subjects, marks aur totals ki list fetch karna
        subjects = request.POST.getlist('subjects[]')
        obtained_marks = request.POST.getlist('marks[]')
        total_marks = request.POST.getlist('totals[]')

        try:
            student_obj = Student.objects.get(id=student_id)
            
            
            for i in range(len(subjects)):
                if subjects[i].strip(): 
                    Result.objects.create(
                        student=student_obj,
                        subject_name=subjects[i],
                        total_marks=total_marks[i],
                        obtained_marks=obtained_marks[i],
                        semester=sem
                    )
            
            messages.success(request, f"All subjects for {student_obj.name} have been saved.")
            return redirect('view_result')
            
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

    return render(request, 'add_result_form.html', {'students': students})


from .models import MessTransaction, Student, Payment  
def fee_records(request):
    """
    Fee Records — course-wise and student-wise fee management.

    - Add a FeePayment entry for a chosen student (amount, fee_type, status).
    - Filter existing records by course, student, or fee type.
    - See totals at a glance.
    """
    # Faculty / admin only
    if not _is_faculty(request.user):
        return redirect('admin_login')

    # ---------- POST: save a new fee entry ----------
    if request.method == "POST" and 'save_payment' in request.POST:
        student_id = request.POST.get('student_id')
        amount = request.POST.get('amount')
        fee_type = request.POST.get('fee_type') or 'Tuition'
        status = request.POST.get('status') or 'Paid'

        try:
            student_obj = Student.objects.get(id=student_id)
            amount_val = decimal.Decimal(amount)

            FeePayment.objects.create(
                student=student_obj,
                amount=amount_val,
                fee_type=fee_type,
                status=status,
            )
            messages.success(
                request,
                f"Fee entry of ₹{amount_val} recorded for {student_obj.name} ({fee_type})."
            )
        except Student.DoesNotExist:
            messages.error(request, "Selected student was not found.")
        except (decimal.InvalidOperation, TypeError, ValueError):
            messages.error(request, "Please enter a valid amount.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

        return redirect('fee_records')

    # ---------- GET: build filtered list ----------
    qs = FeePayment.objects.select_related('student').order_by('-date_paid', '-id')

    # Filters from query params
    filter_course = request.GET.get('course', '').strip()
    filter_student = request.GET.get('student', '').strip()
    filter_type = request.GET.get('fee_type', '').strip()
    filter_status = request.GET.get('status', '').strip()

    if filter_course:
        qs = qs.filter(student__course__istartswith=filter_course)
    if filter_student:
        qs = qs.filter(student__id=filter_student)
    if filter_type:
        qs = qs.filter(fee_type=filter_type)
    if filter_status:
        qs = qs.filter(status=filter_status)

    import datetime as _dt
    today = _dt.date.today()

    total_collected = qs.aggregate(t=Sum('amount'))['t'] or 0
    today_collection = FeePayment.objects.filter(date_paid=today).aggregate(t=Sum('amount'))['t'] or 0
    pending_count = FeePayment.objects.exclude(status='Paid').count()

    context = {
        'records': qs,
        'students': Student.objects.all().order_by('name'),
        'courses': Course.objects.all().order_by('course_name'),
        'fee_types': FeePayment.FEE_TYPES,
        'status_choices': ['Paid', 'Pending', 'Failed'],
        'total_count': qs.count(),
        'total_collected': total_collected,
        'today_collection': today_collection,
        'pending_count': pending_count,
        'filter_course': filter_course,
        'filter_student': filter_student,
        'filter_type': filter_type,
        'filter_status': filter_status,
    }
    return render(request, 'fee_records.html', context)

from django.db import IntegrityError 
from .models import Course, Subject 
def add_subject(request, course_id):
    
    course = get_object_or_404(Course, id=course_id)
    
    if request.method == 'POST':
        name = request.POST.get('subject_name')
        code = request.POST.get('subject_code')
        credits = request.POST.get('credits')
        
        try:
            Subject.objects.create(
                course=course,
                subject_name=name,
                subject_code=code,
                credit_hours=credits 
            )
            messages.success(request, f"Subject '{name}' added to {course.course_name}.")
            return redirect('courses_page')
            
        except IntegrityError:
            
            messages.error(request, "This subject code is already assigned to another subject.")
        except Exception as e:
            messages.error(request, f"Something went wrong: {e}")

    return render(request, 'add_subject.html', {'course': course})

from django.shortcuts import render
from .models import Event # <--- Ye zaroori hai

# ... aapke baaki views ...

def event_list(request):
    events = Event.objects.all() # Ab Python ko pata hai Event kya hai
    return render(request, 'events.html', {'events': events})

# campus/views.py
from django.shortcuts import redirect
from .models import Event, EventRegistration
from django.contrib import messages

def register_event(request, event_id):
    if request.method == "POST":
        event = Event.objects.get(id=event_id)
        name = request.POST.get('name')
        roll = request.POST.get('roll')
        email = request.POST.get('email')
        branch = request.POST.get('branch')

        # Data Save karna
        registration = EventRegistration.objects.create(
            event=event,
            student_name=name,
            roll_number=roll,
            email=email,
            branch=branch
        )
        messages.success(request, f"Registration successful for {event.title}.")
        return redirect('events_page') # Wapas events page par bhej do