from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Students
    path('students/', views.students_page, name='students_page'),
    path('edit-student/<int:pk>/', views.edit_student, name='edit_student'),
    path('delete-student/<int:pk>/', views.delete_student, name='delete_student'),
    path('students/add/', views.add_student, name='add_student'),
    
    # Faculty
    path('faculty/', views.faculty_page, name='faculty_page'),
    path('faculty/delete/<int:id>/', views.delete_faculty, name='delete_faculty'),
    path('faculty/edit/<int:id>/', views.edit_faculty, name='edit_faculty'),
    path('add-faculty/', views.add_faculty, name='add_faculty'),
    
    # Courses
    path('courses/', views.courses_page, name='courses_page'),
    path('course/update/<int:pk>/', views.update_course, name='update_course'),
    path('course/delete/<int:pk>/', views.delete_course, name='delete_course'),
    path('course/add/', views.add_course, name='add_course'),
    path('course/<int:course_id>/add-subject/', views.add_subject, name='add_subject'),
    
    # Attendance
    path('attendance/', views.mark_attendance, name='mark_attendance'),
    path('attendance-report/', views.view_attendance, name='view_attendance'),
    
    # ID Cards & Scanner
    path('qr-scanner/', views.qr_scanner_view, name='qr_scanner'),
    path('my-id-card/', views.student_id_card_view, name='my_id_card'),
    path('all-id-cards/', views.all_id_cards, name='all_id_cards'),
    
    # --- YAHAN DEKHO: Error isi line ki wajah se aa raha tha, maine add kar di hai ---
    path('student-id-card/<int:pk>/', views.student_id_card_view, name='student_id_card'), 
    
    # Library & Mess
    path('library-scanner/', views.library_scanner, name='library_scanner'),
    path('issue-book-api/', views.issue_book_api, name='issue_book_api'),
    path('mess-wallet/', views.mess_scanner, name='mess_scanner'),
    path('mess-payment-api/', views.mess_payment_api, name='mess_payment_api'),
    
    # Profile & Exams
    path('student-profile/', views.student_profile_view, name='student_profile'),
    path('exam-portal/', views.exam_portal_view, name='exam_portal'),
    
    # Fees
    path('fees/', views.fees_dashboard, name='fees_dashboard'),
    path('fees/collect/', views.collect_fee, name='collect_fee'),
    path('fees/receipt/<str:receipt_no>/', views.view_receipt, name='view_receipt'),
    
    # Hostel & Others
    path('hostel-dashboard/', views.hostel_dashboard, name='hostel_page'), 
    path('submit-leave/', views.apply_leave, name='apply_leave'),
    path('submit-complaint/', views.submit_complaint, name='submit_complaint'),
    path('submit-payment/', views.submit_payment_ref, name='submit_payment_ref'),
    path('settings/', views.settings_page, name='settings_page'),


    path('check-result/', views.view_result, name='view_result'),
    path('add-result-portal/', views.add_result_web, name='add_result_web'),
    path('master-admin/', views.master_admin, name='master_admin'),
    path('delete-student/<int:student_id>/', views.delete_student, name='delete_student'),
    path('fee-records/', views.fee_records, name='fee_records'),


    
    path('password-reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password-reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),

    path('events/', views.event_list, name='events_page'),
    path('register/<int:event_id>/', views.register_event, name='register_event'),
]

