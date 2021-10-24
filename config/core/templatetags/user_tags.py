from django import template
from adusersapp import utils

register = template.Library()



@register.simple_tag
def change_status(user):
    status = user['userAccountControl']
    if status == 66048 or status == 512:
        result = utils.change_user_state(
            user['distinguishedName'], "disable")
    else:
        result = utils.change_user_state(
            user['distinguishedName'], "enable")
    # result = utils.change_user_state(user['distinguishedName'], "enable")
    return result

@register.simple_tag
def gen_password():
    return utils.password_generator(12)
