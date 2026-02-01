from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group

from .models import CustomUser

admin.site.unregister(Group)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(CustomUser)
class CustomUserAdmin(BaseUserAdmin):
    """
    Админка для кастомной модели пользователя CustomUser.
    Отображается в разделе "ПОЛЬЗОВАТЕЛИ И ГРУППЫ".
    """

    list_display = (
        "email",
        "username",
        "is_staff",
        "is_active",
        "is_manager",
        "date_joined",
    )
    list_filter = ("is_staff", "is_active", "is_manager", "groups")
    search_fields = ("email", "username")
    ordering = ("email",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Персональная информация", {"fields": ("email", "first_name", "last_name")}),
        (
            "Права доступа",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Дополнительно", {"fields": ("is_manager",)}),
        ("Важные даты", {"fields": ("last_login", "date_joined")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2", "is_manager"),
            },
        ),
    )

    readonly_fields = ("date_joined", "last_login")
