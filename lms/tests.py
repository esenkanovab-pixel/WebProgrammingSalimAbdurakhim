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
from django.urls import reverse
from django.contrib.auth.models import User
from .models import Deadline, Student, Course, Lesson
import json

class DeadlineApiTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='teach', password='t')
        self.teacher.is_staff = True
        self.teacher.save()
        self.course = Course.objects.create(title='C', description='d', teacher=self.teacher)
        self.lesson = Lesson.objects.create(course=self.course, title='L', content='c')
        self.student_user = User.objects.create_user(username='suser', password='p')
        student = Student.objects.create(user=self.student_user)
        # enroll test student in the course for deadline visibility
        student.courses.add(self.course)

    def test_teacher_can_create_deadline_via_api(self):
        self.client.login(username='teach', password='t')
        url = reverse('deadlines_api')
        payload = {'title': 'DL1', 'description':'d', 'due_at': '2030-01-01T12:00:00', 'lesson': self.lesson.id}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('id', data)
        self.assertTrue(Deadline.objects.filter(id=data['id']).exists())

    def test_student_cannot_create_deadline_via_api(self):
        self.client.login(username='suser', password='p')
        url = reverse('deadlines_api')
        payload = {'title': 'DLx', 'description':'d', 'due_at': '2030-01-02T12:00:00'}
        response = self.client.post(url, json.dumps(payload), content_type='application/json')
        # should not be allowed to POST
        self.assertEqual(response.status_code, 403)

    def test_student_can_view_deadlines(self):
        # create a deadline
        dl = Deadline.objects.create(title='Test', description='', due_at='2030-01-03T12:00:00', lesson=self.lesson, created_by=self.teacher)
        self.client.login(username='suser', password='p')
        url = reverse('deadlines_api')
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(any(item['id']==dl.id for item in data.get('deadlines', [])))

    def test_deadlines_shown_on_lesson_page(self):
        dl = Deadline.objects.create(title='LessonDL', description='desc', due_at='2030-02-02T09:00:00', lesson=self.lesson, created_by=self.teacher)
        self.client.login(username='suser', password='p')
        url = reverse('lesson_detail', args=[self.lesson.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'LessonDL')
        self.assertContains(response, 'desc')

    def test_teacher_can_update_deadline_via_api(self):
        dl = Deadline.objects.create(title='Up1', description='old', due_at='2030-03-03T10:00:00', lesson=self.lesson, created_by=self.teacher)
        self.client.login(username='teach', password='t')
        url = reverse('deadline_detail_api', args=[dl.id])
        payload = {'title': 'Up1-mod', 'description': 'new', 'due_at': '2030-03-03T11:00:00', 'lesson': self.lesson.id}
        response = self.client.put(url, json.dumps(payload), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        dl.refresh_from_db()
        self.assertEqual(dl.title, 'Up1-mod')
        self.assertEqual(dl.description, 'new')

    def test_teacher_can_delete_deadline_via_api(self):
        dl = Deadline.objects.create(title='Del1', description='', due_at='2030-04-04T10:00:00', lesson=self.lesson, created_by=self.teacher)
        self.client.login(username='teach', password='t')
        url = reverse('deadline_detail_api', args=[dl.id])
        response = self.client.delete(url)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(Deadline.objects.filter(id=dl.id).exists())

    def test_student_cannot_delete_deadline_via_api(self):
        dl = Deadline.objects.create(title='Del2', description='', due_at='2030-04-04T11:00:00', lesson=self.lesson, created_by=self.teacher)
        self.client.login(username='suser', password='p')
        url = reverse('deadline_detail_api', args=[dl.id])
        response = self.client.delete(url)
        # should not be allowed
        self.assertEqual(response.status_code, 403)

    def test_student_cannot_access_deadline_create_view(self):
        self.client.login(username='suser', password='p')
        url = reverse('deadline_create', args=[self.lesson.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 403)

    def test_student_does_not_see_deadlines_for_other_courses(self):
        # create a different course and lesson with a deadline
        teacher2 = User.objects.create_user(username='t2', password='t')
        course2 = Course.objects.create(title='C2', description='d', teacher=teacher2)
        lesson2 = Lesson.objects.create(course=course2, title='L2', content='c')
        dl2 = Deadline.objects.create(title='Other', description='x', due_at='2030-05-05T10:00:00', lesson=lesson2, created_by=teacher2)

        # suser is enrolled only in self.course
        self.client.login(username='suser', password='p')
        url = reverse('deadlines_api')
        response = self.client.get(url)
        data = response.json()
        self.assertFalse(any(item['id'] == dl2.id for item in data.get('deadlines', [])))

        # access lesson2 page - should not show the deadline to this student
        lesson_url = reverse('lesson_detail', args=[lesson2.id])
        resp2 = self.client.get(lesson_url)
        self.assertEqual(resp2.status_code, 200)
        self.assertNotContains(resp2, 'Other')

class TeacherSubmissionsTests(TestCase):
    def setUp(self):
        self.teacher = User.objects.create_user(username='teach2', password='t')
        self.teacher.is_staff = True
        self.teacher.save()
        self.course = Course.objects.create(title='TeachCourse', description='d', teacher=self.teacher)
        self.lesson = Lesson.objects.create(course=self.course, title='TeachLesson', content='c')

    def test_teacher_can_filter_submissions_by_status(self):
        # create students and submissions with mixed graded status
        s1u = User.objects.create_user(username='studA', password='p')
        s1 = Student.objects.create(user=s1u)
        s1.courses.add(self.course)
        self.course.students.add(s1)
        sub1 = HomeworkSubmission.objects.create(lesson=self.lesson, student=s1, content='a', grade=85, is_graded=True)

        s2u = User.objects.create_user(username='studB', password='p')
        s2 = Student.objects.create(user=s2u)
        s2.courses.add(self.course)
        self.course.students.add(s2)
        sub2 = HomeworkSubmission.objects.create(lesson=self.lesson, student=s2, content='b', is_graded=False)

        self.client.login(username='teach2', password='t')
        url = reverse('teacher_lesson_submissions', args=[self.lesson.id])
        resp = self.client.get(url + '?graded=no')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'studB')
        self.assertNotContains(resp, 'studA')

    def test_pagination_of_submissions(self):
        # create 12 students and submissions
        for i in range(12):
            u = User.objects.create_user(username=f'st{i}', password='p')
            student = Student.objects.create(user=u)
            student.courses.add(self.course)
            self.course.students.add(student)
            HomeworkSubmission.objects.create(lesson=self.lesson, student=student, content=f'content {i}')

        self.client.login(username='teach2', password='t')
        url = reverse('teacher_lesson_submissions', args=[self.lesson.id])
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, 200)
        # page_obj available in context
        page_obj = resp.context['page_obj']
        self.assertEqual(page_obj.paginator.count, 12)
        self.assertEqual(len(page_obj.object_list), 10)
        # check second page has remaining 2
        resp2 = self.client.get(url + '?page=2')
        page_obj2 = resp2.context['page_obj']
        self.assertEqual(len(page_obj2.object_list), 2)

