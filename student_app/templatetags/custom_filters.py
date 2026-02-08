from django import template

register = template.Library()

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Get an item from a dictionary-like object by key"""
    if dictionary is None:
        return None
    if hasattr(dictionary, 'get'):
        return dictionary.get(key)
    return None

@register.filter(name='multiply')
def multiply(value, arg):
    """Multiply the value by argument"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter(name='divide')
def divide(value, arg):
    """Divide the value by argument"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0

@register.filter(name='replace')
def replace_filter(value, arg):
    """Replace characters in string"""
    if '-' in arg:
        old, new = arg.split('-')
        return str(value).replace(old, new)
    return value
