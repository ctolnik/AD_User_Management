from django.urls import path
from . import views


app_name = 'adusersapp'

urlpatterns = [
    path('', views.index, name='index'),
    path('search/', views.users_list, name='users_list_url'),

    path(
        'attribute_detail/<str:attribute>/<path:value>',
        views.attribute_detail, name='attribute_detail'),

    path(
        'user_detail/<str:ad_user>/',
        views.user_detail,
        name='user_detail_url'),

    path(
        'enable_user/<str:ad_user>/',
        views.enable_user, name='enable_user_url'),

    path(
        'disable_user/<str:ad_user>/',
        views.disable_user, name='disable_user_url'),

    path(
        'groups_list/',
        views.groups_list, name='groups_list_url'),

]