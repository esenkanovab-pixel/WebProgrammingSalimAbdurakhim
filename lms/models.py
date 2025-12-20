from django.db import models
from django.contrib.auth.models import User

class Course(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(User, on_delete=models.CASCADE, related_name='teaching_courses')
    students = models.ManyToManyField('Student', blank=True, related_name='enrolled_courses')

    def __str__(self):
        return self.title

class Lesson(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = models.TextField()

    def __str__(self):
        return f"{self.title} ({self.course.title})"

class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    courses = models.ManyToManyField(Course, blank=True, related_name='students_set')

    def __str__(self):
        return self.user.get_full_name() or self.user.username

class HomeworkSubmission(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='submissions')
    content = models.TextField()
    is_graded = models.BooleanField(default=False)
    grade = models.IntegerField(null=True, blank=True)

    def __str__(self):
        return f"Submission by {self.student} for {self.lesson}"

class SubmissionFile(models.Model):
    submission = models.ForeignKey(HomeworkSubmission, on_delete=models.CASCADE, related_name='files')
    file = models.FileField(upload_to='submissions/%Y/%m/%d/')
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"File for {self.submission} - {self.file.name}"

class LessonAttachment(models.Model):
    lesson = models.ForeignKey(Lesson, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='lesson_attachments/%Y/%m/%d/')
    uploaded_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Attachment for {self.lesson} - {self.file.name}"

class Deadline(models.Model):
    """Represents a deadline that may be attached to a lesson (optional)."""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_at = models.DateTimeField()
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL, related_name='deadlines')
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL, related_name='created_deadlines')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_at']

    def __str__(self):
        target = f" for {self.lesson}" if self.lesson else ""
        return f"{self.title}{target} - due {self.due_at.isoformat()}"

class Certificate(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    issued_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Certificate for {self.student} - {self.course.title}"
