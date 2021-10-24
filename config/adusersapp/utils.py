import base64
import secrets
import string
from configparser import ConfigParser

import ldap3
from django.conf import settings
from ldap3.extend.microsoft.addMembersToGroups import \
    ad_add_members_to_groups as addUsersInGroups
from ldap3.extend.microsoft.removeMembersFromGroups import \
    ad_remove_members_from_groups as removeUsersInGroups

AD_LOGIN = settings.AUTH_LDAP_BIND_DN
AD_PASSWORD = settings.AUTH_LDAP_BIND_PASSWORD
DC = settings.AUTH_LDAP_SERVER_URI
AD_SERVER = ldap3.Server(DC, get_info=ldap3.ALL, use_ssl=True)
BASE_DN = settings.AUTH_LDAP_USER_SEARCH.base_dn
# Глубина пути DN до OU где находятся группы. 
ROOT_DEEP_DN = 5
ATTRIBUTES = [
    'sAMAccountName', 'cn', 'telephoneNumber',
    'thumbnailPhoto', 'department', 'userAccountControl', 
    'title', 'company', 'employeeID', 'lastLogon',
    'whenChanged', 'whenCreated', 'mail', 'manager',
    'displayName', 'distinguishedName', 'lastLogon',
    'badPasswordTime', 'badPwdCount',]
FS_GROUPS_DN = """O"""
GROUPS_DN = """OU=Группы,OU"""
COMPANY = 'АО "ss"'


def AD_connection():
    server = AD_SERVER
    return ldap3.Connection(server, user=AD_LOGIN,
                      password=AD_PASSWORD,
                      auto_bind=True)


def search_object(name_attr, value_attr):
    search_filter = f'{name_attr}={value_attr}'
    with AD_connection() as connection:
        connection.search(
            BASE_DN,
            f'(&(objectclass=person)({search_filter}))',
            attributes=ATTRIBUTES)
    return connection.entries


def search_objects(
    dn=BASE_DN, category="person", scope=ldap3.SUBTREE,
    attrs=ATTRIBUTES, name_attr=None, value_attr=None):
    search_filter = None
    if name_attr and value_attr:
        if '(' in value_attr:
            value_attr = value_attr.replace('(', '\\28')
        if ')' in value_attr:
            value_attr = value_attr.replace(')', '\\29')
        
        search_filter = f'{name_attr}={value_attr}'
    if search_filter:
        with AD_connection() as connection:
            connection.search(
                dn,
                f'(&(objectClass={category})({search_filter}))',
                scope, attributes=attrs),
    else:
        with AD_connection() as connection:
            connection.search(
                dn,
                f'(objectClass={category})', scope, attributes=attrs),
    return connection.entries


def search_user_by_FIO(search_user):
    return search_object("cn", f"*{search_user}*")


def search_user_by_cn(search_user):
    return search_object("cn", f"{search_user}*")


def get_user(login):
    return search_object("sAMAccountName", login)[0]


def all_users():
    return search_object("company", COMPANY)


def all_groups():
    return search_objects(GROUPS_DN, 'group', attrs=['cn', 'description'])

def get_groups_in_ou(ou_dn):
    return search_objects(ou_dn, 'group', ldap3.SUBTREE, ['cn', 'description'])


def get_child_ou(ou_dn):
    return search_objects(ou_dn, 'organizationalUnit', ldap3.LEVEL, ['name', ])


def build_ou_topology(root_ou_dn=GROUPS_DN):
    visited_OUs = set()
    topology = {}
    todo = []
    todo.append(root_ou_dn)
    
    while len(todo) > 0:
        current_ou = todo.pop(0)
        child = get_child_ou(current_ou)
        current_ou = current_ou.split(',')[0].split('=')[-1]
        children_names = [ou.name.value for ou in child]
        if not child:
            continue
        for name in children_names:
            if name in topology.items():
                print('in topology')
        topology[current_ou] = children_names
        for ou in child:
            todo.append(ou.entry_dn)
    tree= {}
    for root_ou in topology:
        tree[root_ou] = {}
        for ou in topology[root_ou]:
            tree[root_ou][ou] = {}
            if ou in topology:
                tree[root_ou][ou] = topology[ou]
        break
    return tree[root_ou]


def remove_from_group(dn, group_dn):
    with AD_connection() as connection:
        return removeUsersInGroups(connection, dn, group_dn, fix=True)


def add_to_group(dn, group_dn):
    with AD_connection() as connection:
        return addUsersInGroups(connection, dn, group_dn)


def generate_context_data(account):
    dict = {}
    for key, value in account.entry_attributes_as_dict.items():
        if key == 'thumbnailPhoto' and len(value) > 0:
            dict[key] = base64.b64encode(value[0]).decode("utf-8")
        elif key == 'manager' and len(value) > 0:
            dict[key] = value[0].split('=')[1].split(',')[0]
        else:
            if len(value) > 0:
                dict[key] = value[0]
            else:
                dict[key] = None
    return dict



def get_group(groups_dn):
    result = []
    with AD_connection() as connection:
        for group in groups_dn:
            if '(' in group:
                group = group.replace('(', '\\28')
            if ')' in group:
                group = group.replace(')', '\\29')
            connection.search(
                BASE_DN, f'(&(objectClass=group)(distinguishedName={group}))', attributes=['cn', 'description'])
            result.append(connection.entries[0])
    return result


def get_specific_groups():
    inet_OU ='OU=Ch'
    KAV_OU = 'OU='
    PRNT_OU = "OU="
    inet_groups = get_groups_in_ou(inet_OU)
    kav_groups = get_groups_in_ou(KAV_OU)
    fs_groups = get_groups_in_ou(FS_GROUPS_DN)
    printers_groups = get_groups_in_ou(PRNT_OU)
    result = {
        'Internet': inet_groups,
        'KAV': kav_groups,
        'File Access': fs_groups,
        'Printers': printers_groups,
        
    }
    return result


def get_membership(member):
    with AD_connection() as connection:
        connection.search(
            BASE_DN,
            f"(member={member})", attributes=['cn', 'description'])
    return connection.entries


def change_user_state(distinguishedName, status='enable'):
    codes = {
        'enable': 512,
        'disable': 514
    }
    code = codes[status]
    with AD_connection() as connection:
        if connection.compare(
            distinguishedName, 'userAccountControl', code
        ):
            return True
        connection.modify(
            distinguishedName,
            {'userAccountControl': (ldap3.MODIFY_REPLACE, code)})
    return connection


def switch_user_state(distinguishedName, code=[512]):
    with AD_connection() as connection:
        if connection.compare(
            'userAccountControl', code
        ):
            print("enabed")


def password_generator(length):
    alphabet = string.ascii_letters + string.digits
    while True:
        password = ''.join(secrets.choice(alphabet) for i in range(length))
        if (any(c.islower() for c in password)
                and any(c.isupper() for c in password)
                and sum(c.isdigit() for c in password) >= 3):
            break
    return password


def change_password(dn, new_password):
    with AD_connection() as connection:
        connection.start_tls()
        change = connection.extend.microsoft.modify_password(user=dn,
                                           new_password=new_password)
    if change:
        return connection.result['description']
    return connection.result['message']
