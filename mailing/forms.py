from django import forms

from .models import Client, Mailing, Message


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["email", "full_name", "comment"]
        widgets = {
            "comment": forms.Textarea(attrs={"rows": 4}),
        }
        labels = {
            "email": "Email",
            "full_name": "Ф.И.О.",
            "comment": "Комментарий",
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ["subject", "body"]
        widgets = {
            "body": forms.Textarea(attrs={"rows": 8}),
        }
        labels = {
            "subject": "Тема письма",
            "body": "Тело письма",
        }


class MailingForm(forms.ModelForm):
    class Meta:
        model = Mailing
        fields = ["start_time", "end_time", "message", "clients"]
        widgets = {
            "start_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }
        labels = {
            "start_time": "Дата и время первой отправки",
            "end_time": "Дата и время окончания отправки",
            "message": "Сообщение",
            "clients": "Получатели",
        }
