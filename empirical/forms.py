from django import forms

class PostForm(forms.Form):
    json = forms.FileField(required=True)
    file = forms.FileField(required=False)