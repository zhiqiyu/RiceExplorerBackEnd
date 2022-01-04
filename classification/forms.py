from django import forms

class PostForm(forms.Form):
    json = forms.FileField(required=True)
    boundary_file = forms.FileField(required=False)
    samples = forms.FileField(required=True)
    