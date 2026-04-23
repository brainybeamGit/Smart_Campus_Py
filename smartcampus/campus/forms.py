from django import forms
from .models import Course, Student

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = '__all__'

class CourseForm(forms.ModelForm):  # <--- Ye naam check kar
    class Meta:
        model = Course
        fields = '__all__' # Ya phir fields = ['course_name', 'course_code']