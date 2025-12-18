from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Lesson, Student, HomeworkSubmission
from .forms import CourseCreateForm, LessonCreateForm, HomeworkSubmissionForm, GradeForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
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
        student = getattr(request.user, 'student_profile', None)
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
def course_create(request):
    if not is_teacher(request.user):
        raise PermissionDenied
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
def lesson_create(request, course_id):
    if not is_teacher(request.user):
        raise PermissionDenied
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
    student = getattr(request.user, 'student_profile', None)
    if student:
        course.students.add(student)
        student.courses.add(course)
    return redirect('course_detail', course_id=course.id)


@login_required
def student_dashboard(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        return redirect('course_list')
    # gather enrolled courses and submissions
    courses = student.courses.all().prefetch_related('lessons')
    submissions = HomeworkSubmission.objects.filter(student=student).select_related('lesson')
    submissions_by_lesson = {s.lesson_id: s for s in submissions}

    courses_data = []
    for course in courses:
        lessons_data = []
        for lesson in course.lessons.all():
            lessons_data.append({
                'lesson': lesson,
                'submission': submissions_by_lesson.get(lesson.id)
            })
        courses_data.append({'course': course, 'lessons': lessons_data})

    return render(request, 'student_dashboard.html', {
        'student': student,
        'courses_data': courses_data,
    })


@login_required
def submission_delete(request, submission_id):
    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    # only owner can delete
    if getattr(request.user, 'student_profile', None) != submission.student:
        return redirect('student_dashboard')
    if request.method == 'POST':
        lesson_id = submission.lesson.id
        submission.delete()
        return redirect('lesson_detail', lesson_id=lesson_id)
    return render(request, 'submission_confirm_delete.html', {'submission': submission})


@login_required
def submission_edit(request, submission_id):
    submission = get_object_or_404(HomeworkSubmission, id=submission_id)
    if getattr(request.user, 'student_profile', None) != submission.student:
        return redirect('student_dashboard')
    if request.method == 'POST':
        form = HomeworkSubmissionForm(request.POST, instance=submission)
        if form.is_valid():
            form.save()
            return redirect('lesson_detail', lesson_id=submission.lesson.id)
    else:
        form = HomeworkSubmissionForm(instance=submission)
    return render(request, 'submission_form.html', {'form': form, 'submission': submission})


@login_required
def submissions_list(request):
    student = getattr(request.user, 'student_profile', None)
    if not student:
        return redirect('course_list')

    qs = HomeworkSubmission.objects.filter(student=student).select_related('lesson', 'lesson__course')

    # filters: course, graded (yes/no), q search by lesson title
    course_id = request.GET.get('course')
    graded = request.GET.get('graded')
    q = request.GET.get('q')
    if course_id:
        qs = qs.filter(lesson__course_id=course_id)
    if graded == 'yes':
        qs = qs.filter(is_graded=True)
    elif graded == 'no':
        qs = qs.filter(is_graded=False)
    if q:
        qs = qs.filter(Q(lesson__title__icontains=q) | Q(lesson__course__title__icontains=q))

    # pagination
    paginator = Paginator(qs.order_by('-id'), 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # list of student's courses for filter choices
    courses = student.courses.all()

    return render(request, 'submissions_list.html', {
        'page_obj': page_obj,
        'courses': courses,
        'filter_course': course_id,
        'filter_graded': graded,
        'q': q,
    })

@login_required
def grade_submission(request, submission_id):
    if not is_teacher(request.user):
        raise PermissionDenied
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
