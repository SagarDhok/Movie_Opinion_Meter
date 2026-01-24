# movies/templatetags/movie_filters.py
"""
Custom Django template filters for movie app.

Usage in templates:
    {% load movie_filters %}
    {{ vote_percents|get_item:'bad' }}
"""

from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Get item from dictionary using key.
    
    Django templates don't support dictionary[key] syntax,
    so we use this filter instead.
    
    Args:
        dictionary: Dict to get value from
        key: Key to lookup
        
    Returns:
        Value from dictionary or 0 if key doesn't exist
        
    Example:
        {{ vote_percents|get_item:'good' }}
    """
    if dictionary is None:
        return 0
    return dictionary.get(key, 0)


@register.filter
def split(value, arg):
    """
    Split string by delimiter.
    
    Args:
        value: String to split
        arg: Delimiter
        
    Returns:
        List of split strings
        
    Example:
        {% for item in "a,b,c"|split:"," %}
    """
    return value.split(arg)