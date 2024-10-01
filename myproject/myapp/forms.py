from django import forms

class PostForm(forms.Form):
    image = forms.ImageField(label='Image')
    text = forms.CharField(widget=forms.Textarea, required=False, label='Text')
