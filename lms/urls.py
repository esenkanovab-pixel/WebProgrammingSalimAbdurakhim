from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.course_list, name='course_list'),
    path('register/', views.register_user, name='register_user'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='course_list'), name='logout'),
    path('course/create/', views.course_create, name='course_create'),
    path('course/<int:course_id>/', views.course_detail, name='course_detail'),
    path('course/<int:course_id>/lesson/create/', views.lesson_create, name='lesson_create'),
    path('lesson/<int:lesson_id>/', views.lesson_detail, name='lesson_detail'),
    path('course/<int:course_id>/enroll/', views.course_enroll, name='course_enroll'),
    path('submission/<int:submission_id>/grade/', views.grade_submission, name='grade_submission'),
]
