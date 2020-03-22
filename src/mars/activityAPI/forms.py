from django import forms

class Control(forms.Form):
    device_id = forms.IntegerField(required=True)
    action = forms.CharField(max_length=5, required=True)
    type = forms.CharField(max_length=50, required=False)
    repo = forms.CharField(required=False)
    commit = forms.CharField(required=False)

