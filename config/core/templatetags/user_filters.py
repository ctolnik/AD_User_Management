from django import template
from adusersapp import utils

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})

# @register.filter
# def change_password(user):
#     result = utils.change_password(user)
#     return result