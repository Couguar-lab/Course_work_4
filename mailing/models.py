import uuid

from django.contrib.auth.models import User
from django.db import models


class Client(models.Model):
    email = models.EmailField(unique=True, verbose_name="Email")
    full_name = models.CharField(max_length=300, verbose_name="Ф.И.О.")
    comment = models.TextField(blank=True, null=True, verbose_name="Комментарий")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Владелец", null=True, blank=True
    )

    def __str__(self):
        return f"{self.full_name} <{self.email}>"

    class Meta:
        app_label = "mailing"
        verbose_name = "Получатель"
        verbose_name_plural = "Получатели"
        ordering = ["full_name"]


class Message(models.Model):
    subject = models.CharField(max_length=255, verbose_name="Тема письма")
    body = models.TextField(verbose_name="Тело письма")
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Владелец", null=True, blank=True
    )

    def __str__(self):
        return self.subject

    class Meta:
        app_label = "mailing"
        verbose_name = "Сообщение"
        verbose_name_plural = "Сообщения"


class Mailing(models.Model):
    STATUS_CHOICES = [
        ("created", "Создана"),
        ("launched", "Запущена"),
        ("completed", "Завершена"),
    ]

    start_time = models.DateTimeField(verbose_name="Дата и время первой отправки")
    end_time = models.DateTimeField(verbose_name="Дата и время окончания отправки")
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="created", verbose_name="Статус"
    )
    message = models.ForeignKey(
        Message,
        on_delete=models.CASCADE,
        related_name="mailings",
        verbose_name="Сообщение",
    )
    clients = models.ManyToManyField(
        Client, related_name="mailings", verbose_name="Получатели"
    )
    owner = models.ForeignKey(
        User, on_delete=models.CASCADE, verbose_name="Владелец", null=True, blank=True
    )

    def __str__(self):
        return f"Рассылка: {self.message.subject} ({self.get_status_display()})"

    class Meta:
        app_label = "mailing"
        verbose_name = "Рассылка"
        verbose_name_plural = "Рассылки"
        ordering = ["-start_time"]


class Attempt(models.Model):
    STATUS_CHOICES = [
        ("success", "Успешно"),
        ("failure", "Не успешно"),
    ]

    timestamp = models.DateTimeField(
        auto_now_add=True, verbose_name="Дата и время попытки"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, verbose_name="Статус попытки"
    )
    server_response = models.TextField(
        blank=True, null=True, verbose_name="Ответ почтового сервера"
    )
    mailing = models.ForeignKey(
        Mailing,
        on_delete=models.CASCADE,
        related_name="attempts",
        verbose_name="Рассылка",
    )

    def __str__(self):
        return (
            f"{self.timestamp.strftime('%d.%m.%Y %H:%M')} — {self.get_status_display()}"
        )

    class Meta:
        app_label = "mailing"
        verbose_name = "Попытка рассылки"
        verbose_name_plural = "Попытки рассылок"
        ordering = ["-timestamp"]


class ActivationToken(models.Model):
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="activation_token"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Токен активации для {self.user.username}"

    class Meta:
        app_label = "mailing"
