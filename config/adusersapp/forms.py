from django import forms

class SearchUserForm(forms.Form):
    FIO = forms.CharField(max_length=200, label="ФИО пользователя")

class GroupUserSelectForm(forms.Form):
    group = forms.BooleanField()
    
class ManageUserForm(forms.Form):
    status = forms.BooleanField()
