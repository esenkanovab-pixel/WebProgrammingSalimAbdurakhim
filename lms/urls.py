from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .forms import LoginForm

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('register/', views.register_user, name='register_user'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html', authentication_form=LoginForm), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='course_list'), name='logout'),
    path('course/create/', views.course_create, name='course_create'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/lesson/create/', views.lesson_create, name='lesson_create'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('lesson/<int:lesson_id>/attachments/add/', views.lesson_add_attachment, name='lesson_add_attachment'),
    path('lesson/attachment/<int:attachment_id>/delete/', views.lesson_attachment_delete, name='lesson_attachment_delete'),
    path('course/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('submission/<int:submission_id>/delete/', views.submission_delete, name='submission_delete'),
    path('submission/<int:submission_id>/edit/', views.submission_edit, name='submission_edit'),
    path('submission/file/<int:file_id>/delete/', views.submission_file_delete, name='submission_file_delete'),
    path('submissions/', views.submissions_list, name='submissions_list'),
    # Deadlines and calendar
    path('lesson/<int:lesson_id>/deadline/create/', views.deadline_create, name='deadline_create'),
    path('deadline/<int:deadline_id>/edit/', views.deadline_edit, name='deadline_edit'),
    path('deadline/<int:deadline_id>/delete/', views.deadline_delete, name='deadline_delete'),
    path('calendar/', views.calendar_view, name='calendar_view'),
    # API
    path('api/deadlines/', views.deadlines_api, name='deadlines_api'),
    path('api/deadlines/<int:deadline_id>/', views.deadline_detail_api, name='deadline_detail_api'),
]
