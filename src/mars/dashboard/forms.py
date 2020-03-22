from django import forms

class UserAPICreate(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    write_checkbox = forms.BooleanField(required=False)
    read_checkbox = forms.BooleanField(required=False)
    user_id = forms.IntegerField(required=False)

class CreateAccount(forms.Form):
    password = forms.CharField(max_length=72, required=True)
    username = forms.CharField(max_length=150, required=True)
    fname = forms.CharField(max_length=30, required=False)
    lname = forms.CharField(max_length=150, required=False)
    staff_checkbox = forms.BooleanField(required=False)

class EditAccount(forms.Form):
    password = forms.CharField(max_length=72, required=False)
    username = forms.CharField(max_length=150, required=True)
    fname = forms.CharField(max_length=30, required=False)
    lname = forms.CharField(max_length=150, required=False)
    staff_checkbox = forms.BooleanField(required=False)
    user_id = forms.IntegerField(required=False)

class NewDevice(forms.Form):
    name = forms.CharField(max_length=50, required=True)
    d_type = forms.CharField(max_length=50, required=True)
    user_id = forms.IntegerField(required=False)
    device_id = forms.IntegerField(required=False)