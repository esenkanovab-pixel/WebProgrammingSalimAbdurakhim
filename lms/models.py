from django.db import models
from django.contrib.auth.models import User
import uuid
from django.db.models.signals import post_save
from django.dispatch import receiver
import os

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
    """Certificate issued to a student for a course.

    Fields:
    - certificate_id: unique UUID for verification
    - student, course: relations
    - issued_at: timestamp of issue
    - pdf_file: generated PDF saved under media/certificates/generated/
    """
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='certificates')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='certificates')
    certificate_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    issued_at = models.DateTimeField(auto_now_add=True)
    pdf_file = models.FileField(upload_to='certificates/generated/', null=True, blank=True)

    def __str__(self):
        return f"Certificate {self.certificate_id} for {self.student} - {self.course.title}"

    def generate_certificate_files(self):
        """Generate a PNG with text overlay and a PDF containing this image.

        Try to use ReportLab for PDF creation; if it's not available, fall back to
        Pillow's PDF saving. Save PDF into media/certificates/ (in 'generated' subfolder).
        If the PDF already exists, skip regeneration.
        """
        from django.conf import settings
        from django.core.files import File as DjangoFile
        from PIL import Image, ImageDraw, ImageFont
        from django.utils import timezone

        template_path = os.path.join(settings.MEDIA_ROOT, 'certificates', 'templates', 'background.png')
        if not os.path.exists(template_path):
            return

        out_dir = os.path.join(settings.MEDIA_ROOT, 'certificates', 'generated')
        os.makedirs(out_dir, exist_ok=True)

        pdf_filename = f"certificate-{self.id}.pdf"
        pdf_path = os.path.join(out_dir, pdf_filename)

        # If PDF already exists on disk and field points to it, skip generation
        if self.pdf_file and self.pdf_file.name:
            try:
                if os.path.exists(os.path.join(settings.MEDIA_ROOT, self.pdf_file.name)):
                    return
            except Exception:
                pass
        if os.path.exists(pdf_path):
            # Attach existing file to model if not attached
            if not (self.pdf_file and self.pdf_file.name):
                with open(pdf_path, 'rb') as f:
                    self.pdf_file.save(pdf_filename, DjangoFile(f), save=True)
            return

        # Open base image and draw
        img = Image.open(template_path).convert('RGBA')
        draw = ImageDraw.Draw(img)
        w, h = img.size

        student_name = self.student.user.get_full_name() or self.student.user.username
        course_title = self.course.title
        teacher_name = self.course.teacher.get_full_name() or self.course.teacher.username
        date_str = (self.issued_at or timezone.now()).strftime('%d.%m.%Y')
        id_str = str(self.certificate_id)

        try:
            font_large = ImageFont.truetype('arial.ttf', size=int(w*0.045))
            font_medium = ImageFont.truetype('arial.ttf', size=int(w*0.03))
            font_small = ImageFont.truetype('arial.ttf', size=int(w*0.018))
        except Exception:
            font_large = ImageFont.load_default()
            font_medium = ImageFont.load_default()
            font_small = ImageFont.load_default()

        def draw_centered(text, y_frac, font, fill=(0,0,0)):
            try:
                bbox = draw.textbbox((0, 0), text, font=font)
                text_w = bbox[2] - bbox[0]
                text_h = bbox[3] - bbox[1]
            except Exception:
                # fallback for older/newer Pillow versions
                try:
                    text_w, text_h = font.getsize(text)
                except Exception:
                    text_w, text_h = (0, 0)
            x = (w - text_w) / 2
            y = int(h * y_frac) - text_h/2
            draw.text((x, y), text, font=font, fill=fill)

        draw_centered(student_name, 0.36, font_large)
        draw_centered(course_title, 0.48, font_medium)
        draw_centered(f"Instructor: {teacher_name}", 0.78, font_small)
        draw.text((int(w*0.06), int(h*0.9)), f"Certificate ID: {id_str}", font=font_small, fill=(0,0,0))
        draw.text((int(w*0.76), int(h*0.9)), f"Date: {date_str}", font=font_small, fill=(0,0,0))

        img_filename = f"certificate-{self.id}.png"
        img_path = os.path.join(out_dir, img_filename)
        img.convert('RGB').save(img_path, 'PNG')

        # Try ReportLab first
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            c = canvas.Canvas(pdf_path, pagesize=(w, h))
            c.drawImage(ImageReader(img_path), 0, 0, width=w, height=h)
            c.showPage()
            c.save()
        except Exception:
            # Fallback: Pillow's PDF save
            try:
                img_rgb = Image.open(img_path).convert('RGB')
                img_rgb.save(pdf_path, 'PDF', resolution=100.0)
            except Exception:
                # If PDF generation fails, clean up and exit
                try:
                    if os.path.exists(img_path):
                        os.remove(img_path)
                except Exception:
                    pass
                return

        # Attach PDF to model
        try:
            with open(pdf_path, 'rb') as f:
                self.pdf_file.save(pdf_filename, DjangoFile(f), save=True)
        except Exception:
            return


@receiver(post_save, sender=HomeworkSubmission)
def create_certificate_on_course_complete(sender, instance, **kwargs):
    """Create a Certificate automatically when a student has graded submissions
    for all lessons of a course (simple definition of course completion).
    This runs whenever a submission is saved; it only acts when submission is graded.
    """
    # Only consider graded submissions
    if not instance.is_graded:
        return
    student = instance.student
    course = instance.lesson.course

    # If course has no lessons, don't issue a certificate
    lessons = course.lessons.all()
    if not lessons.exists():
        return

    # Ensure there is a graded submission for each lesson by this student
    for lesson in lessons:
        sub = HomeworkSubmission.objects.filter(student=student, lesson=lesson, is_graded=True).first()
        if not sub:
            return

    # If we get here, student completed the course -> create certificate if not exists
    cert, created = Certificate.objects.get_or_create(student=student, course=course)
    if created:
        # generate image and PDF and attach to the record
        cert.generate_certificate_files()
