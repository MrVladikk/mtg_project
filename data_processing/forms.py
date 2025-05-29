from django import forms

class CSVUploadForm(forms.Form):
    csv_file = forms.FileField(label='Выберите CSV файл')
    # Вы можете добавить другие поля в форму, если это необходимо, например:
    # description = forms.CharField(label='Описание файла (необязательно)', required=False)
