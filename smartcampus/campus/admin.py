from django import forms
from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Sum

from .models import (
    Student, Faculty, Course, Subject, Attendance, Notice,
    Book, BookIssue, MessWallet, MessTransaction, MessMenu,
    ExamSchedule, Result, FeePayment, FeeTransaction,
    HostelRoom, Complaint, LeaveApplication, Payment,
    Event, EventRegistration,
)

# ---------------------------------------------------------------------------
# Admin site branding
# ---------------------------------------------------------------------------
admin.site.site_header = "SmartCampus Administration"
admin.site.site_title = "SmartCampus Admin"
admin.site.index_title = "Campus Management Dashboard"


# ---------------------------------------------------------------------------
# Inlines
# ---------------------------------------------------------------------------
class SubjectInline(admin.TabularInline):
    model = Subject
    extra = 1
    fields = ('subject_name', 'subject_code', 'credit_hours')


class FeePaymentInline(admin.TabularInline):
    model = FeePayment
    extra = 0
    readonly_fields = ('receipt_no', 'date_paid')
    fields = ('receipt_no', 'fee_type', 'amount', 'status', 'date_paid')


# ---------------------------------------------------------------------------
# Student
# ---------------------------------------------------------------------------
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_no', 'name', 'course', 'photo_preview', 'qr_preview')
    list_display_links = ('roll_no', 'name')
    search_fields = ('name', 'roll_no', 'course')
    list_filter = ('course',)
    readonly_fields = ('qr_preview_large',)
    fieldsets = (
        ('Student Info', {
            'fields': ('name', 'roll_no', 'course', 'photo')
        }),
        ('QR Code', {
            'fields': ('qr_code', 'qr_preview_large'),
            'classes': ('collapse',),
        }),
    )
    inlines = [FeePaymentInline]

    @admin.display(description='Photo')
    def photo_preview(self, obj):
        if obj.photo:
            return format_html(
                '<img src="{}" style="height:40px;width:40px;border-radius:50%;object-fit:cover;" />',
                obj.photo.url,
            )
        return "—"

    @admin.display(description='QR')
    def qr_preview(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="height:40px;width:40px;" />', obj.qr_code.url)
        return "—"

    @admin.display(description='QR Code Preview')
    def qr_preview_large(self, obj):
        if obj.qr_code:
            return format_html('<img src="{}" style="height:180px;width:180px;" />', obj.qr_code.url)
        return "QR will generate on save."


# ---------------------------------------------------------------------------
# Faculty  (with login-account fields)
# ---------------------------------------------------------------------------
class FacultyAdminForm(forms.ModelForm):
    """Custom form that adds username/password fields for creating a Faculty login."""
    username = forms.CharField(
        max_length=150,
        required=True,
        help_text="Login username for this faculty member.",
    )
    password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Leave blank to keep the existing password (on edit). Required when creating.",
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(render_value=False),
        required=False,
        help_text="Re-enter the password to confirm.",
    )

    class Meta:
        model = Faculty
        fields = ('name', 'department', 'subject', 'email', 'phone')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-fill username from linked user when editing
        if self.instance and self.instance.pk and self.instance.user:
            self.fields['username'].initial = self.instance.user.username
            self.fields['password'].required = False
        else:
            self.fields['password'].required = True
            self.fields['confirm_password'].required = True

    def clean(self):
        cleaned = super().clean()
        username = cleaned.get('username')
        pw = cleaned.get('password')
        cpw = cleaned.get('confirm_password')

        if pw or cpw:
            if pw != cpw:
                raise forms.ValidationError("Passwords do not match.")

        if username:
            qs = User.objects.filter(username=username)
            if self.instance and self.instance.pk and self.instance.user_id:
                qs = qs.exclude(pk=self.instance.user_id)
            if qs.exists():
                raise forms.ValidationError(f"Username '{username}' is already taken.")
        return cleaned


@admin.register(Faculty)
class FacultyAdmin(admin.ModelAdmin):
    form = FacultyAdminForm
    list_display = ('name', 'username_display', 'department', 'subject', 'email', 'has_login')
    search_fields = ('name', 'department', 'subject', 'email', 'user__username')
    list_filter = ('department',)
    fieldsets = (
        ('Faculty Info', {
            'fields': ('name', 'department', 'subject', 'email', 'phone')
        }),
        ('Login Credentials', {
            'description': "These credentials let the faculty member sign in to the Admin Portal.",
            'fields': ('username', 'password', 'confirm_password'),
        }),
    )

    @admin.display(description='Username')
    def username_display(self, obj):
        return obj.user.username if obj.user else "—"

    @admin.display(description='Login', boolean=True)
    def has_login(self, obj):
        return obj.user is not None

    def save_model(self, request, obj, form, change):
        username = form.cleaned_data.get('username')
        password = form.cleaned_data.get('password')

        if obj.user:
            user = obj.user
            user.username = username
            user.email = obj.email or user.email
            user.is_staff = True
            if password:
                user.set_password(password)
            user.save()
        else:
            user = User.objects.create_user(
                username=username,
                email=obj.email or '',
                password=password or User.objects.make_random_password(),
            )
            user.is_staff = True
            user.save()
            obj.user = user

        # Put the user in the Faculty group
        faculty_group, _ = Group.objects.get_or_create(name='Faculty')
        user.groups.add(faculty_group)

        super().save_model(request, obj, form, change)


# ---------------------------------------------------------------------------
# Course + Subject
# ---------------------------------------------------------------------------
@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('course_code', 'course_name', 'faculty', 'subject_count')
    list_display_links = ('course_code', 'course_name')
    search_fields = ('course_name', 'course_code', 'faculty__name')
    list_filter = ('faculty',)
    inlines = [SubjectInline]

    @admin.display(description='Subjects')
    def subject_count(self, obj):
        return obj.subjects.count()


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('subject_code', 'subject_name', 'course', 'credit_hours')
    list_display_links = ('subject_code', 'subject_name')
    search_fields = ('subject_name', 'subject_code', 'course__course_name')
    list_filter = ('course', 'credit_hours')


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student', 'course', 'date', 'status', 'is_present')
    list_filter = ('status', 'date', 'course')
    search_fields = ('student__name', 'student__roll_no', 'course__course_name')
    date_hierarchy = 'date'
    list_editable = ('status', 'is_present')
    autocomplete_fields = ('student', 'course')


# ---------------------------------------------------------------------------
# Notice
# ---------------------------------------------------------------------------
@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_urgent', 'date_posted')
    list_filter = ('is_urgent', 'date_posted')
    search_fields = ('title', 'message')
    list_editable = ('is_urgent',)
    date_hierarchy = 'date_posted'


# ---------------------------------------------------------------------------
# Library
# ---------------------------------------------------------------------------
@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ('book_id', 'title', 'author', 'is_issued', 'issued_to')
    list_filter = ('is_issued',)
    search_fields = ('title', 'author', 'book_id')
    autocomplete_fields = ('issued_to',)


@admin.action(description="Mark selected book issues as returned")
def mark_as_returned(modeladmin, request, queryset):
    queryset.update(is_returned=True)


@admin.register(BookIssue)
class BookIssueAdmin(admin.ModelAdmin):
    list_display = ('student', 'book_name', 'issue_date', 'return_date', 'is_returned')
    list_filter = ('is_returned', 'issue_date', 'return_date')
    search_fields = ('student__name', 'student__roll_no', 'book_name')
    date_hierarchy = 'issue_date'
    autocomplete_fields = ('student',)
    actions = [mark_as_returned]


# ---------------------------------------------------------------------------
# Mess
# ---------------------------------------------------------------------------
@admin.register(MessWallet)
class MessWalletAdmin(admin.ModelAdmin):
    list_display = ('student', 'balance', 'last_transaction')
    search_fields = ('student__name', 'student__roll_no')
    readonly_fields = ('last_transaction',)
    autocomplete_fields = ('student',)


@admin.register(MessTransaction)
class MessTransactionAdmin(admin.ModelAdmin):
    list_display = ('student', 'amount', 'meal_type', 'date')
    list_filter = ('meal_type', 'date')
    search_fields = ('student__name', 'student__roll_no')
    date_hierarchy = 'date'
    autocomplete_fields = ('student',)


@admin.register(MessMenu)
class MessMenuAdmin(admin.ModelAdmin):
    list_display = ('day', 'breakfast', 'lunch', 'dinner')
    list_editable = ('breakfast', 'lunch', 'dinner')
    search_fields = ('day', 'breakfast', 'lunch', 'dinner')


# ---------------------------------------------------------------------------
# Exam & Result
# ---------------------------------------------------------------------------
@admin.register(ExamSchedule)
class ExamScheduleAdmin(admin.ModelAdmin):
    list_display = ('subject_name', 'course', 'exam_date', 'exam_time', 'room_no')
    list_filter = ('exam_date', 'course')
    search_fields = ('subject_name', 'course__course_name', 'room_no')
    date_hierarchy = 'exam_date'


@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display = ('student', 'subject_name', 'semester', 'obtained_marks', 'total_marks', 'percentage')
    list_filter = ('semester', 'subject_name')
    search_fields = ('student__name', 'student__roll_no', 'subject_name')
    autocomplete_fields = ('student',)

    @admin.display(description='%')
    def percentage(self, obj):
        pct = obj.get_percentage()
        color = 'green' if pct >= 60 else ('orange' if pct >= 40 else 'red')
        return format_html('<b style="color:{};">{:.1f}%</b>', color, pct)


# ---------------------------------------------------------------------------
# Fees
# ---------------------------------------------------------------------------
@admin.register(FeePayment)
class FeePaymentAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'student', 'fee_type', 'amount', 'status', 'date_paid')
    list_filter = ('fee_type', 'status', 'date_paid')
    search_fields = ('receipt_no', 'student__name', 'student__roll_no')
    readonly_fields = ('receipt_no', 'date_paid')
    date_hierarchy = 'date_paid'
    autocomplete_fields = ('student',)

    def changelist_view(self, request, extra_context=None):
        response = super().changelist_view(request, extra_context)
        try:
            qs = response.context_data['cl'].queryset
            response.context_data['total_collected'] = qs.aggregate(t=Sum('amount'))['t'] or 0
        except (AttributeError, KeyError):
            pass
        return response


@admin.register(FeeTransaction)
class FeeTransactionAdmin(admin.ModelAdmin):
    list_display = ('receipt_no', 'student', 'category', 'amount', 'status', 'date')
    list_filter = ('category', 'status', 'date')
    search_fields = ('receipt_no', 'student__name', 'student__roll_no')
    date_hierarchy = 'date'
    autocomplete_fields = ('student',)


# ---------------------------------------------------------------------------
# Hostel
# ---------------------------------------------------------------------------
@admin.register(HostelRoom)
class HostelRoomAdmin(admin.ModelAdmin):
    list_display = ('room_number', 'block', 'student')
    list_filter = ('block',)
    search_fields = ('room_number', 'block', 'student__username')


@admin.action(description="Mark selected complaints as resolved")
def mark_resolved(modeladmin, request, queryset):
    queryset.update(is_resolved=True)


@admin.register(Complaint)
class ComplaintAdmin(admin.ModelAdmin):
    list_display = ('user', 'category', 'is_resolved', 'created_at')
    list_filter = ('category', 'is_resolved', 'created_at')
    search_fields = ('user__username', 'description')
    list_editable = ('is_resolved',)
    date_hierarchy = 'created_at'
    actions = [mark_resolved]


@admin.action(description="Approve selected leave applications")
def approve_leave(modeladmin, request, queryset):
    queryset.update(status='Approved')


@admin.action(description="Reject selected leave applications")
def reject_leave(modeladmin, request, queryset):
    queryset.update(status='Rejected')


@admin.register(LeaveApplication)
class LeaveApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'start_date', 'end_date', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'created_at')
    search_fields = ('user__username', 'reason')
    list_editable = ('status',)
    date_hierarchy = 'start_date'
    actions = [approve_leave, reject_leave]


# ---------------------------------------------------------------------------
# Payments (generic)
# ---------------------------------------------------------------------------
@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('student', 'txn_id', 'amount', 'status', 'date')
    list_filter = ('status', 'date')
    search_fields = ('txn_id', 'student__username')
    list_editable = ('status',)
    date_hierarchy = 'date'


# ---------------------------------------------------------------------------
# Events
# ---------------------------------------------------------------------------
class EventRegistrationInline(admin.TabularInline):
    model = EventRegistration
    extra = 0
    readonly_fields = ('registration_date',)
    fields = ('student_name', 'roll_number', 'email', 'branch', 'registration_date')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('title', 'date', 'time', 'location', 'image_preview', 'registration_count')
    search_fields = ('title', 'location', 'description')
    list_filter = ('date', 'location')
    readonly_fields = ('created_at',)
    inlines = [EventRegistrationInline]

    @admin.display(description='Image')
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="height:50px;border-radius:4px;" />', obj.image.url)
        return "—"

    @admin.display(description='Registered')
    def registration_count(self, obj):
        return obj.eventregistration_set.count()


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = ('student_name', 'roll_number', 'event', 'branch', 'email', 'registration_date')
    list_filter = ('event', 'branch', 'registration_date')
    search_fields = ('student_name', 'roll_number', 'email', 'event__title')
    date_hierarchy = 'registration_date'
    autocomplete_fields = ('event',)
