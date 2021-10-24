import base64

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from . import utils
from .forms import SearchUserForm


@login_required
def index(request):
    template_name = "adusersapp/index.html"
    bound_form = SearchUserForm(request.POST or None)
    if bound_form.is_valid():
        filter = bound_form.cleaned_data
        ad_users = utils.search_user_by_FIO(filter['FIO'])
        template_name = 'adusersapp/user_list.html'
        users = []
        for ad_user in ad_users:
            user = utils.generate_context_data(ad_user)
            users.append(user)
        context = {
            'users': users,
            }
        return render(request, template_name, context=context)
    context = {'form': bound_form}
    return render(request, template_name, context=context)


@login_required
def users_list(request):
    template = "adusersapp/user_list.html"
    search_query = request.GET.get('search_cn', '')
    if search_query:
        ad_users = utils.search_user_by_cn(search_query)
    else:
        ad_users = utils.all_users()
    
    bound_form = SearchUserForm(request.POST or None)
    if bound_form.is_valid():
        filter = bound_form.cleaned_data['FIO']
        ad_users = utils.search_user_by_cn(filter)
    users = []
    for ad_user in ad_users:
        user = utils.generate_context_data(ad_user)
        users.append(user)
    context = {
        'users': users,
        }
    return render(request, template, context=context)


@login_required
def user_detail(request, ad_user):
    template_name = "adusersapp/user_detail.html"
    ad_user = utils.get_user(ad_user)
    update_groups = None
    password_query = request.GET.get('new_password', '')
    new_pass = None
    if password_query:
        new_pass = utils.change_password(ad_user.entry_dn, password_query)
    
    member_of_group = utils.get_membership(ad_user.distinguishedName.value)
    membership_ad = set([i.entry_dn for i in member_of_group])
    if len(request.GET) >= 1:
        membership_request = set([dn for _, dn in request.GET.items()])
        exlude_groups = list(membership_ad.difference(membership_request))
        include_groups = list(membership_request.difference(membership_ad))
        if exlude_groups:
            for group in exlude_groups:
                update_groups = utils.remove_from_group(ad_user.entry_dn, group)
        if include_groups:
            for group in include_groups:
                update_groups = utils.add_to_group(ad_user.entry_dn, group)
        if update_groups:
            member_of_group = utils.get_membership(ad_user.distinguishedName.value)
    specific_groups = utils.get_specific_groups()
    uniq_spec_groups = set()
    for groups in specific_groups.values():
        for group in groups:
            uniq_spec_groups.add(group.entry_dn)
        
    diff_groups = membership_ad.difference(uniq_spec_groups)
    if diff_groups:
        other_groups = utils.get_group(diff_groups)
    groups = {**{'Others': other_groups}, **specific_groups}
    
    user = utils.generate_context_data(ad_user)
    context = {
        'user': user,
        'member_of_group': member_of_group,
        'groups': groups,
        'pass': new_pass,
            }
    return render(request, template_name, context=context)

@login_required
def enable_user(request, ad_user):
    obj  = utils.get_user(ad_user)
    utils.change_user_state(obj.entry_dn, 'enable')
    return redirect("adusersapp:user_detail_url", ad_user=ad_user)

@login_required
def disable_user(request, ad_user):
    obj  = utils.get_user(ad_user)
    utils.change_user_state(obj.entry_dn, 'disable')
    return redirect("adusersapp:user_detail_url", ad_user=ad_user)

@login_required
def attribute_detail(request, attribute, value):
    template_name = "adusersapp/user_list.html"
    # if "(" in value:
    #     value = value.split("(")[0].strip()
    objects = utils.search_objects(name_attr=attribute, value_attr=value)
    users = []
    for object in objects:
        user = utils.generate_context_data(object)
        users.append(user)
    context = {
            'users': users,
            }
    return render(request, template_name, context=context)


@login_required
def groups_list(request):
    template = "adusersapp/groups_list.html"
    
    inet_group = utils.group_management()
    context = {
        'groups': 'groups',
        'OUs': 'OUs'
        }
    return render(request, template, context=context)
