from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Template filter to get item from dictionary by key"""
    return dictionary.get(key)

@register.filter
def add(value, arg):
    """Add the arg to the value."""
    try:
        return int(value) + int(arg)
    except (ValueError, TypeError):
        try:
            return value + arg
        except:
            return ''
