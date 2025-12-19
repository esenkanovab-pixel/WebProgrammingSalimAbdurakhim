from .models import Deadline
from django.shortcuts import get_object_or_404
from django.http import Http404
from django.db import DatabaseError

def get_all_deadlines():
    try:
        return Deadline.objects.select_related('lesson', 'created_by').all()
    except DatabaseError:
        # Table might not exist or DB unavailable — return empty queryset safely
        return Deadline.objects.none()

def get_deadline(pk):
    try:
        return get_object_or_404(Deadline, id=pk)
    except DatabaseError:
        # treat DB issues as not found
        raise Http404("Deadline not found")

def create_deadline(**kwargs):
    try:
        return Deadline.objects.create(**kwargs)
    except DatabaseError:
        return None

def update_deadline(instance, **kwargs):
    try:
        for k, v in kwargs.items():
            setattr(instance, k, v)
        instance.save()
        return instance
    except DatabaseError:
        return None

def delete_deadline(instance):
    try:
        instance.delete()
    except DatabaseError:
        pass