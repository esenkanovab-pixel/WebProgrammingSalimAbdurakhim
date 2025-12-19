from .models import Deadline
from django.shortcuts import get_object_or_404

def get_all_deadlines():
    return Deadline.objects.select_related('lesson', 'created_by').all()

def get_deadline(pk):
    return get_object_or_404(Deadline, id=pk)

def create_deadline(**kwargs):
    return Deadline.objects.create(**kwargs)

def update_deadline(instance, **kwargs):
    for k, v in kwargs.items():
        setattr(instance, k, v)
    instance.save()
    return instance

def delete_deadline(instance):
    instance.delete()