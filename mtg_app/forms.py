from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django import forms
from .models import Card,Deck

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True, help_text="Введите действующий email.")

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")

class CardForm(forms.ModelForm):
    class Meta:
        model = Card
        fields = ['name', 'set', 'quantity', 'image_url']  # При необходимости добавьте другие поля
        
class DeckForm(forms.ModelForm):
    class Meta:
        model = Deck
        fields = ['name', 'description', 'cards']  # Поля формы

    # Если нужно настроить виджет для поля cards (например, выбор нескольких карт)
    cards = forms.ModelMultipleChoiceField(
        queryset=Card.objects.all(),
        widget=forms.CheckboxSelectMultiple,  # Виджет для выбора нескольких карт
        required=False
    )