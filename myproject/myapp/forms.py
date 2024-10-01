from django import forms

class PostForm(forms.Form):
    image = forms.CharField(widget=forms.Textarea, label='Image URL')
    text = forms.CharField(widget=forms.Textarea, required=False, label='Text')
