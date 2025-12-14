from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login
from .models import Course, Lesson, Student, HomeworkSubmission
from .forms import CourseCreateForm, LessonCreateForm, HomeworkSubmissionForm, GradeForm, UserRegistrationForm

def course_list(request):
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})

def course_detail(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    lessons = course.lessons.all()
    return render(request, 'course_detail.html', {'course': course, 'lessons': lessons})

def lesson_detail(request, lesson_id):
    lesson = get_object_or_404(Lesson, id=lesson_id)
    student = None
    submission = None
    form = None
    if request.user.is_authenticated:
        student = getattr(request.user, 'student_profile', None)
        if student:
            submission = HomeworkSubmission.objects.filter(lesson=lesson, student=student).first()
            if request.method == 'POST':
                form = HomeworkSubmissionForm(request.POST, instance=submission)
                if form.is_valid():
                    hw = form.save(commit=False)
                    hw.lesson = lesson
                    hw.student = student
                    hw.save()
                    return redirect('lesson_detail', lesson_id=lesson.id)
            else:
                form = HomeworkSubmissionForm(instance=submission)
    return render(request, 'lesson_detail.html', {
        'lesson': lesson,
        'submission': submission,
        'form': form,
    })

@login_required
def course_create(request):
    if request.method == 'POST':
        form = CourseCreateForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()
            return redirect('course_detail', course_id=course.id)
    else:
        form = CourseCreateForm()
    return render(request, 'course_form.html', {'form': form})

@login_required
def lesson_create(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    if course.teacher != request.user:
        return redirect('course_detail', course_id=course.id)
    if request.method == 'POST':
        form = LessonCreateForm(request.POST)
        if form.is_valid():
            lesson = form.save(commit=False)
            lesson.course = course
            lesson.save()
            return redirect('lesson_detail', lesson_id=lesson.id)
    else:
        form = LessonCreateForm()
    return render(request, 'lesson_form.html', {'form': form, 'course': course})

@login_required
def course_enroll(request, course_id):
    course = get_object_or_404(Course, id=course_id)
    student = getattr(request.user, 'student_profile', None)
    if student:
        course.students.add(student)
        student.courses.add(course)
    return redirect('course_detail', course_id=course.id)

@login_required
def grade_submission(request, submission_id):
    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    if submission.lesson.course.teacher != request.user:
        return redirect('lesson_detail', lesson_id=submission.lesson.id)
    if request.method == 'POST':
        form = GradeForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
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
