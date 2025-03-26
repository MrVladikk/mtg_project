from django import forms
from .models import Thread, Post

class ThreadForm(forms.ModelForm):
    class Meta:
        model = Thread
        fields = ['title']
        widgets = {'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Заголовок темы'}),}
        
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']
        widgets = {'content': forms.Textarea(attrs={'class': 'form-control', 'placeholder': 'Ваше сообщение', 'rows': 4}),}