from django.contrib import admin
from .models import Course, Lesson, Student, HomeworkSubmission, Certificate, Deadline, SubmissionFile, LessonAttachment

admin.site.register(Course)
admin.site.register(Lesson)
admin.site.register(Student)
admin.site.register(HomeworkSubmission)
admin.site.register(SubmissionFile)
admin.site.register(LessonAttachment)
admin.site.register(Certificate)
admin.site.register(Deadline)
