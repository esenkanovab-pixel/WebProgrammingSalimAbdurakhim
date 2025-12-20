import hashlib
from django import template

register = template.Library()

@register.filter
def gravatar_url(user, size=80):
    """Return the gravatar image URL for a user (by email)."""
    email = getattr(user, 'email', '') or ''
    email_hash = hashlib.md5(email.strip().lower().encode('utf-8')).hexdigest()
    return f"https://www.gravatar.com/avatar/{email_hash}?s={size}&d=identicon"
