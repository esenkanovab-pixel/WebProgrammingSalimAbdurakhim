from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Student, Course, Lesson, HomeworkSubmission


class AuthAndStudentFlowTests(TestCase):
    def test_registration_creates_student_and_logs_in(self):
        url = reverse('register_user')
        data = {
            'username': 'stud1',
            'first_name': 'Иван',
            'last_name': 'Иванов',
            'email': 'stud1@example.com',
            'password': 'pass1234',
            'role': 'student',
        }
        response = self.client.post(url, data, follow=True)
        # user created and redirected to course list
        self.assertTrue(User.objects.filter(username='stud1').exists())
        user = User.objects.get(username='stud1')
        # Student profile should exist
        self.assertTrue(Student.objects.filter(user=user).exists())
        # logged in
        self.assertEqual(int(self.client.session['_auth_user_id']), user.pk)

    def test_login_view_accepts_credentials(self):
        u = User.objects.create_user(username='u1', password='secret')
        url = reverse('login')
        response = self.client.post(url, {'username': 'u1', 'password': 'secret'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(int(self.client.session['_auth_user_id']), u.pk)

    def test_student_can_submit_and_delete_homework(self):
        # setup teacher, course, lesson, student
        teacher = User.objects.create_user(username='t', password='t')
        course = Course.objects.create(title='C1', description='d', teacher=teacher)
        lesson = Lesson.objects.create(course=course, title='L1', content='content')

        user = User.objects.create_user(username='s1', password='p')
        student = Student.objects.create(user=user)
        # enroll both sides
        student.courses.add(course)
        course.students.add(student)

        # login student
        self.client.login(username='s1', password='p')

        # submit homework via lesson detail POST
        url = reverse('lesson_detail', args=[lesson.id])
        response = self.client.post(url, {'content': 'my answer'}, follow=True)
        self.assertEqual(response.status_code, 200)
        sub = HomeworkSubmission.objects.filter(lesson=lesson, student=student).first()
        self.assertIsNotNone(sub)
        self.assertEqual(sub.content, 'my answer')

        # delete submission
        del_url = reverse('submission_delete', args=[sub.id])
        response = self.client.post(del_url, follow=True)
        self.assertFalse(HomeworkSubmission.objects.filter(id=sub.id).exists())

    def test_student_dashboard_shows_courses_and_status(self):
        teacher = User.objects.create_user(username='t2', password='t')
        course = Course.objects.create(title='CourseX', description='d', teacher=teacher)
        lesson = Lesson.objects.create(course=course, title='LessonX', content='c')

        user = User.objects.create_user(username='s2', password='p')
        student = Student.objects.create(user=user)
        student.courses.add(course)
        course.students.add(student)

        # create a submission
        HomeworkSubmission.objects.create(lesson=lesson, student=student, content='answer')

        self.client.login(username='s2', password='p')
        url = reverse('student_dashboard')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        # ensure dashboard context contains courses_data
        self.assertIn('courses_data', response.context)
        self.assertTrue(any(entry['course'].id == course.id for entry in response.context['courses_data']))

    def test_student_cannot_access_teacher_views(self):
        # create a student user
        user = User.objects.create_user(username='no_teacher', password='p')
        Student.objects.create(user=user)
        self.client.login(username='no_teacher', password='p')

        # try to access course_create (teacher-only)
        url = reverse('course_create')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

        # try to access lesson_create (teacher-only) with dummy course id
        # create a teacher and course to have an id
        t = User.objects.create_user(username='tt', password='t')
        course = Course.objects.create(title='c', description='d', teacher=t)
        url2 = reverse('lesson_create', args=[course.id])
        response2 = self.client.get(url2)
        self.assertEqual(response2.status_code, 403)
from django.test import TestCase

# Create your tests here.
