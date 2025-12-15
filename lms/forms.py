from django import forms
from django.contrib.auth.models import User
from .models import Course, Lesson, HomeworkSubmission, Student

ROLE_CHOICES = (
    ('student', 'Студент'),
    ('teacher', 'Преподаватель'),
)

class UserRegistrationForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class':'form-control'}))
    role = forms.ChoiceField(choices=ROLE_CHOICES, widget=forms.RadioSelect)

    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name', 'email', 'password']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password'])
        role = self.cleaned_data['role']
        if role == 'teacher':
            user.is_staff = True
        if commit:
            user.save()
            if role == 'student':
                Student.objects.create(user=user)
        return user

class CourseCreateForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'description': forms.Textarea(attrs={'class':'form-control'}),
        }

class LessonCreateForm(forms.ModelForm):
    class Meta:
        model = Lesson
        fields = ['title', 'content']
        widgets = {
            'title': forms.TextInput(attrs={'class':'form-control'}),
            'content': forms.Textarea(attrs={'class':'form-control'}),
        }

class HomeworkSubmissionForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={'class':'form-control'}),
        }

class GradeForm(forms.ModelForm):
    class Meta:
        model = HomeworkSubmission
        fields = ['grade']
        widgets = {
            'grade': forms.NumberInput(attrs={'class':'form-control', 'min':0, 'max':100}),
        }
