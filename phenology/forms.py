from django import forms

class SettingsForm(forms.Form):
    json = forms.FileField(required=True)
    file = forms.FileField(required=False)
    