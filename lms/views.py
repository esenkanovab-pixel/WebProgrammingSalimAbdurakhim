from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Lesson, Student, HomeworkSubmission
from .forms import CourseCreateForm, LessonCreateForm, HomeworkSubmissionForm, GradeForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import login

def is_teacher(user):
    return user.is_staff

def course_list(request):
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    return render(request, 'course_detail.html', {'course': course, 'lessons': lessons})

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    submission = None
    if request.user.is_authenticated:
        student = getattr(request.user, 'student', None)
        if student:
            submission = HomeworkSubmission.objects.filter(lesson=lesson, student=student).first()
            if request.method == 'POST':
                form = HomeworkSubmissionForm(request.POST, instance=submission)
                if form.is_valid():
                    obj = form.save(commit=False)
                    obj.student = student
                    obj.lesson = lesson
                    obj.save()
                    return redirect('lesson_detail', lesson_id=lesson.id)
            else:
                form = HomeworkSubmissionForm(instance=submission)
        else:
            form = None
    else:
        form = None
    return render(request, 'lesson_detail.html', {'lesson': lesson, 'form': form, 'submission': submission})

@login_required
@user_passes_test(is_teacher)
def course_create(request):
    if request.method == 'POST':
        form = CourseCreateForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect('course_list')
    else:
        form = CourseCreateForm()
    return render(request, 'course_form.html', {'form': form})

@login_required
@user_passes_test(is_teacher)
def lesson_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if request.method == 'POST':
        form = LessonCreateForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = LessonCreateForm()
    return render(request, 'lesson_form.html', {'form': form, 'course': course})

@login_required
def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = getattr(request.user, 'student', None)
    if student:
        course.students.add(student)
        student.courses.add(course)
    return redirect('course_detail', course_id=course.id)

@login_required
@user_passes_test(is_teacher)
def grade_submission(request, submission_id):
    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=submission)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.is_graded = True
            obj.save()
            return redirect('lesson_detail', lesson_id=submission.lesson.id)
    else:
        form = GradeForm(instance=submission)
    return render(request, 'grade_form.html', {'form': form, 'submission': submission})

def register_user(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('course_list')
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})
