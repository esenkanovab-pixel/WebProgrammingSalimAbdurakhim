from django.shortcuts import render, redirect, get_object_or_404
from .models import Course, Lesson, Student, HomeworkSubmission
from .forms import CourseCreateForm, LessonCreateForm, HomeworkSubmissionForm, GradeForm, UserRegistrationForm
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.db.models import Q
from django.contrib.auth import login
from django.utils import timezone

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

    # collect upcoming deadlines for student's courses
    from django.utils import timezone
    now = timezone.now()
    deadlines = get_all_deadlines().filter(lesson__course__in=courses, due_at__gte=now).select_related('lesson')[:50]

    return render(request, 'student_dashboard.html', {
        'student': student,
        'courses_data': courses_data,
        'deadlines': deadlines,
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

# -- Deadline management and API -------------------------------------------------
from django.http import JsonResponse, HttpResponseBadRequest, HttpResponseNotAllowed
from django.views.decorators.http import require_http_methods
from .forms import DeadlineForm
from .models import Deadline
from .repositories import get_all_deadlines, get_deadline, create_deadline, update_deadline, delete_deadline
import json

@login_required
@require_http_methods(['GET','POST'])
def deadlines_api(request):
    """Return list of deadlines as JSON. POST allows teachers to create a deadline using JSON or form-encoded data."""
    if request.method == 'GET':
        qs = get_all_deadlines()
        data = []
        for d in qs:
            data.append({
                'id': d.id,
                'title': d.title,
                'description': d.description,
                'due_at': d.due_at.isoformat(),
                'lesson_id': d.lesson.id if d.lesson else None,
                'lesson_title': d.lesson.title if d.lesson else None,
                'created_by': d.created_by.username if d.created_by else None,
            })
        return JsonResponse({'deadlines': data})

    # POST: create
    if not is_teacher(request.user):
        return HttpResponseNotAllowed(['GET'])
    # accept JSON or form data
    try:
        payload = json.loads(request.body.decode('utf-8')) if request.body else request.POST.dict()
    except Exception:
        return HttpResponseBadRequest('invalid json')
    form = DeadlineForm(payload)
    if form.is_valid():
        dl = form.save(commit=False)
        dl.created_by = request.user
        dl.save()
        return JsonResponse({'status': 'created', 'id': dl.id})
    return JsonResponse({'errors': form.errors}, status=400)

@login_required
@require_http_methods(['GET', 'PUT', 'DELETE'])
def deadline_detail_api(request, deadline_id):
    d = get_deadline(deadline_id)
    if request.method == 'GET':
        return JsonResponse({
            'id': d.id,
            'title': d.title,
            'description': d.description,
            'due_at': d.due_at.isoformat(),
            'lesson_id': d.lesson.id if d.lesson else None,
            'lesson_title': d.lesson.title if d.lesson else None,
            'created_by': d.created_by.username if d.created_by else None,
        })

    # PUT and DELETE require teacher
    if not is_teacher(request.user):
        return HttpResponseNotAllowed(['GET'])

    if request.method == 'DELETE':
        delete_deadline(d)
        return JsonResponse({'status': 'deleted'})

    # handle PUT - update
    if request.method == 'PUT':
        try:
            payload = json.loads(request.body.decode('utf-8'))
        except Exception:
            return HttpResponseBadRequest('invalid json')
        form = DeadlineForm(payload, instance=d)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.created_by = dl.created_by or request.user
            dl.save()
            return JsonResponse({'status': 'ok', 'id': dl.id})
        else:
            return JsonResponse({'errors': form.errors}, status=400)

@login_required
@require_http_methods(['GET', 'POST'])
def deadline_create(request, lesson_id=None):
    if not is_teacher(request.user):
        raise PermissionDenied
    lesson = None
    if lesson_id:
        lesson = get_object_or_404(Lesson, id=lesson_id)

    if request.method == 'POST':
        form = DeadlineForm(request.POST)
        if form.is_valid():
            dl = form.save(commit=False)
            dl.created_by = request.user
            dl.save()
            return redirect('lesson_detail', lesson_id=dl.lesson.id) if dl.lesson else redirect('course_list')
    else:
        initial = {}
        if lesson:
            initial['lesson'] = lesson
        form = DeadlineForm(initial=initial)
    return render(request, 'deadline_form.html', {'form': form, 'lesson': lesson})

@login_required
@require_http_methods(['GET', 'POST'])
def deadline_edit(request, deadline_id):
    dl = get_object_or_404(Deadline, id=deadline_id)
    if not is_teacher(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        form = DeadlineForm(request.POST, instance=dl)
        if form.is_valid():
            form.save()
            return redirect('lesson_detail', lesson_id=dl.lesson.id) if dl.lesson else redirect('course_list')
    else:
        form = DeadlineForm(instance=dl)
    return render(request, 'deadline_form.html', {'form': form, 'deadline': dl})

@login_required
@require_http_methods(['POST', 'GET'])
def deadline_delete(request, deadline_id):
    dl = get_object_or_404(Deadline, id=deadline_id)
    if not is_teacher(request.user):
        raise PermissionDenied
    if request.method == 'POST':
        lesson_id = dl.lesson.id if dl.lesson else None
        dl.delete()
        return redirect('lesson_detail', lesson_id=lesson_id) if lesson_id else redirect('course_list')
    return render(request, 'deadline_confirm_delete.html', {'deadline': dl})

@login_required
@require_http_methods(['GET'])
def calendar_view(request):
    # Students and teachers can view
    return render(request, 'calendar.html')

