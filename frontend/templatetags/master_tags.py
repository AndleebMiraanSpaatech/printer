from django import template
from django.db.models import Model, Field
import re

# Helper functions:
# ------------------------------------------------------------------------------------------
get_model_name = lambda model: getattr(model, '__name__', model.__class__.__name__)
get_field_name = lambda f: getattr(f, 'name', '')
def pluralize_last_word(sentence):
    words = sentence.split()
    if not words:
        return ""
    word = words[-1]
    if word.endswith(("s", "x", "z", "ch", "sh")):
        word += "es"
    elif word.endswith("y") and word[-2] not in "aeiou":
        word = word[:-1] + "ies"
    elif word.endswith("f"):
        word = word[:-1] + "ves"
    elif word.endswith("fe"):
        word = word[:-2] + "ves"
    elif word.endswith("o") and word[-2] not in "aeiou":
        word += "es"
    else:
        word += "s"
    words[-1] = word
    return " ".join(words)

# ------------------------------------------------------------------------------------------

register = template.Library()

# Custom template filters aka custom tags
# ------------------------------------------------------------------------------------------

# String Manipulation Filters
@register.filter
def sentence_case(obj, flag=None):
    if isinstance(obj, Field): name = obj.name
    elif isinstance(obj, str): name = obj
    elif isinstance(obj, Model):name = obj.__class__.__name__
    sentence = ' '.join(w.capitalize() for w in re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])', name))
    return pluralize_last_word(sentence) if flag == "plural" else sentence


@register.filter
def kebab_case(model):
    return '-'.join(word.lower() for word in re.findall(r'[A-Z][a-z]*', get_model_name(model)))

@register.filter
def pad_center_left(value, total_length=14):
    return f'{"&nbsp;" * ((pad := max(0, total_length - len(str(value or "")))) // 2)}{value or ""}{"&nbsp;" * (pad - pad // 2)}'

@register.filter
def pad_left_one(value, total_length=14):
    return f"&nbsp;{value or ''}{'&nbsp;' * max(0, total_length - 1 - len(str(value or '')))}"


# Python Coding Filters
@register.filter
def model_fields(model):
    return [f for f in model._meta.get_fields() if f.concrete and not f.many_to_many and not f.primary_key]

@register.filter
def normal_fields(model):
    return [ f for f in model._meta.get_fields() if f.concrete and not f.primary_key and not f.is_relation ]
    
@register.filter
def get_value(obj, field):
    return getattr(obj, field.name if hasattr(field, "name") else field, "")

@register.filter
def field_class(field):
    return field.__class__.__name__


@register.filter
def serial_no(counter, page_no):
    page_size = 10
    return (page_no - 1) * page_size + counter

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key, '')

@register.filter
def inner_length(d):
    return sum(len(v) for v in d.values() if isinstance(v, dict))
# ------------------------------------------------------------------------------------------