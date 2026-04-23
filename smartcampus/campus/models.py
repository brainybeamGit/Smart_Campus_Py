from pyexpat.errors import messages
import uuid
from django.db import models

from django.shortcuts import redirect
import qrcode
from io import BytesIO
from django.core.files import File
from PIL import Image
from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta, date

class Student(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='student_profile',
    )
    name = models.CharField(max_length=100)
    roll_no = models.CharField(max_length=50, unique=True)
    course = models.CharField(max_length=100, null=True, blank=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    # Photo ke liye field (ID card ke liye zaroori hai)
    photo = models.ImageField(upload_to='student_photos/', null=True, blank=True)

    # QR Code save karne ke liye
    qr_code = models.ImageField(upload_to='qr_codes/', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.roll_no})"

    def save(self, *args, **kwargs):
        # 1. Pehle check karo agar QR code banana zaroori hai (optimization)
        if not self.qr_code:
            # QR Code ka data taiyar karo
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(self.roll_no)
            qr.make(fit=True)
            
            img = qr.make_image(fill='black', back_color='white')
            
            # 2. Image ko memory mein save karo
            buffer = BytesIO()
            img.save(buffer, format='PNG')
            filename = f'qr-{self.roll_no}.png'
            
            # 3. Field mein file save karo
            self.qr_code.save(filename, File(buffer), save=False)
        
        super().save(*args, **kwargs)

        
# 2. Faculty Model
class Faculty(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='faculty_profile',
    )
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, default="General")
    subject = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)

    def __str__(self):
        return f"Prof. {self.name} - {self.subject}"

# 3. Course Model
class Course(models.Model):
    course_name = models.CharField(max_length=100)
    course_code = models.CharField(max_length=20, unique=True)
    faculty = models.ForeignKey(Faculty, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return f"{self.course_name} ({self.course_code})"

# 4. Attendance Model
class Attendance(models.Model):
    STATUS_CHOICES = [
        ('Present', 'Present'),
        ('Absent', 'Absent'),
        ('Late', 'Late'),
    ]
    
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, null=True, blank=True)
    # Allow the date to be set explicitly (was auto_now_add which silently ignored
    # the value passed to .create() and always wrote today's date).
    date = models.DateField(default=date.today)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='Present')
    is_present = models.BooleanField(default=True)

    class Meta:
        unique_together = ('student', 'date')

    def __str__(self):
        student_name = self.student.name if self.student else "Unknown Student"
        course_name = self.course.course_name if self.course else "No Course"
        return f"{student_name} - {course_name} ({self.date})"

# Baki Models (Notice, Book, BookIssue) sahi hain... unhe waise hi rehne do.

class Notice(models.Model):
    title = models.CharField(max_length=200)
    message = models.TextField()
    date_posted = models.DateTimeField(auto_now_add=True)
    is_urgent = models.BooleanField(default=False) # Urgent notice red color mein dikhega

    def __str__(self):
        return self.title

class Book(models.Model):
    title = models.CharField(max_length=200)
    book_id = models.CharField(max_length=50, unique=True) # QR Code isi ka banega
    author = models.CharField(max_length=100)
    is_issued = models.BooleanField(default=False)
    issued_to = models.ForeignKey('Student', on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return self.title  
    
    from django.db import models

class BookIssue(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    book_name = models.CharField(max_length=200)
    issue_date = models.DateField(auto_now_add=True)
    return_date = models.DateField()
    is_returned = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if not self.return_date:
            self.return_date = date.today() + timedelta(days=14) # 14 din ka auto-logic
        super().save(*args, **kwargs)

class MessWallet(models.Model):
    student = models.OneToOneField('Student', on_delete=models.CASCADE)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    last_transaction = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.roll_no} - ₹{self.balance}"

class MessTransaction(models.Model):
    student = models.ForeignKey('Student', on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    meal_type = models.CharField(max_length=50, default="Meal")


    # 1. Exam Schedule ke liye

class ExamSchedule(models.Model):
    course = models.ForeignKey('Course', on_delete=models.CASCADE)
    subject_name = models.CharField(max_length=100)
    exam_date = models.DateField()
    exam_time = models.TimeField()
    room_no = models.CharField(max_length=20)

    def __str__(self):
        return f"{self.subject_name} - {self.exam_date}"

class FeePayment(models.Model):
    FEE_TYPES = [
        ('Tuition', 'Tuition Fee'),
        ('Exam', 'Exam Fee'),
        ('Hostel', 'Hostel Fee'),
        ('Library', 'Library Fee'),
    ]

    # ForeignKey Student table se connect karta hai
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    
    # Receipt No automatic banane ke liye (Unique rahega)
    receipt_no = models.CharField(max_length=20, unique=True, editable=False)
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    fee_type = models.CharField(max_length=50, choices=FEE_TYPES)
    date_paid = models.DateField(auto_now_add=True)
    
    # Status: Paid, Pending, ya Failed
    status = models.CharField(max_length=20, default='Paid')

    # Save hone se pehle automatic receipt number generate karega
    def save(self, *args, **kwargs):
        if not self.receipt_no:
            # PAY- student_id - random number
            self.receipt_no = f"PAY-{uuid.uuid4().hex[:6].upper()}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.receipt_no} - {self.student.name}"
    from django.db import models


# 1. Mess Menu Model
class MessMenu(models.Model):
    day = models.CharField(max_length=20)
    breakfast = models.CharField(max_length=200)
    lunch = models.CharField(max_length=200)
    dinner = models.CharField(max_length=200)

    def __str__(self):
        return self.day

# 2. Hostel Room Model
class HostelRoom(models.Model):
    student = models.OneToOneField(User, on_delete=models.CASCADE)
    room_number = models.CharField(max_length=10)
    block = models.CharField(max_length=10)

    def __str__(self):
        return f"Room {self.room_number}"

# 3. Complaint Model (Iska naam 'Complaint' hi rakhna)
class Complaint(models.Model):
    CATEGORY_CHOICES = [
        ('Electricity', 'Electricity'),
        ('Water/Plumbing', 'Water/Plumbing'),
        ('Wi-Fi/Internet', 'Wi-Fi/Internet'),
        ('Other', 'Other'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    description = models.TextField()
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category} - {self.user.username}"

class LeaveApplication(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()
    # Ye nayi line add karo taaki Admin approve kar sake
    status = models.CharField(max_length=20, default='Pending', choices=[
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected')
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.start_date}"
    
def submit_complaint(request):
    if request.method == 'POST':
        cat = request.POST.get('category')
        desc = request.POST.get('description')
        
        # Dhayan se dekho: 'Complaint' model use karna hai, 'HostelComplaint' nahi
        Complaint.objects.create(
            user=request.user,      # Aapke model mein 'user' hai
            category=cat,           # Ab ye error nahi dega kyunki Complaint model mein category hai
            description=desc
        )
        
        messages.success(request, "Complaint registered successfully.")
        return redirect('hostel_page')
    return redirect('hostel_page')



class Payment(models.Model):
    student = models.ForeignKey(User, on_delete=models.CASCADE)
    txn_id = models.CharField(max_length=100)
    amount = models.IntegerField(default=1200)
    status = models.CharField(max_length=20, default='Pending') # Pending, Success, Failed
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student.username} - {self.txn_id}"
    

# --- MERGED RESULT MODEL ---
class Result(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    subject_name = models.CharField(max_length=100) # Pehle wale ka 'subject' aur doosre ka 'subject_name' merge kar diya
    total_marks = models.IntegerField(default=100)
    obtained_marks = models.IntegerField() # 'marks_obtained' aur 'obtained_marks' mein se ye zyada professional hai
    semester = models.IntegerField()

    def __str__(self):
        # Taaki Admin panel mein student ka naam aur subject saaf dikhe
        return f"{self.student.name} - {self.subject_name} (Sem: {self.semester})"
    
    # --- EXTRA PRO TIP (Bhai Special) ---
    # Ek chota sa function jo percentage nikal kar dega
    def get_percentage(self):
        return (self.obtained_marks / self.total_marks) * 100
    
class Subject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='subjects')
    subject_name = models.CharField(max_length=100)
    subject_code = models.CharField(max_length=20, unique=True)
    credit_hours = models.IntegerField(default=3)

    def __clstr__(self):
        return f"{self.subject_name} ({self.course.course_name})"
    
    # campus/models.py mein niche ye add karo
class FeeTransaction(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    receipt_no = models.CharField(max_length=50, unique=True)
    category = models.CharField(max_length=100) # e.g. Tuition, Exam, Hostel
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Success')

    def __str__(self):
        return f"{self.receipt_no} - {self.student.name}"


from django.db import models

class Event(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    image = models.ImageField(upload_to='events/') 
    date = models.CharField(max_length=50) # Example: "15 MAR"
    location = models.CharField(max_length=100)
    # TimeField ko CharField kar diya taaki aap "10:00 AM" likh sako asani se
    time = models.CharField(max_length=50) 
    created_at = models.DateTimeField(auto_now_add=True)

    # Bhai yahan '__clstr__' nahi, '__str__' aayega
    def __str__(self):
        return self.title

# campus/models.py
from django.db import models

class EventRegistration(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    student_name = models.CharField(max_length=100)
    roll_number = models.CharField(max_length=20)
    email = models.EmailField()
    branch = models.CharField(max_length=50)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.student_name} - {self.event.title}"
    

