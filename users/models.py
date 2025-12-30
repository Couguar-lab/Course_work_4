from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """
    Кастомная модель пользователя.
    Использует email как основное поле для аутентификации.
    Добавлено поле is_manager для быстрой проверки роли менеджера.
    """

    email = models.EmailField(
        unique=True,
        verbose_name="Email",
        help_text="Обязательное поле. Уникальный email адрес.",
    )
    is_manager = models.BooleanField(
        default=False,
        verbose_name="Менеджер",
        help_text="Отметьте, если пользователь является менеджером",
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ["email"]

    def __str__(self):
        return self.email
