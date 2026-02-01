from django.contrib import admin

from .models import Attempt, Client, Mailing, Message


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "comment")
    list_filter = ("email",)
    search_fields = ("full_name", "email")


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ("subject", "body_preview")
    search_fields = ("subject", "body")

    def body_preview(self, obj):
        return obj.body[:75] + "..." if len(obj.body) > 75 else obj.body

    body_preview.short_description = "Предпросмотр тела"


@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ("message", "start_time", "end_time", "status", "client_count")
    list_filter = ("status", "start_time", "end_time")
    filter_horizontal = ("clients",)

    def client_count(self, obj):
        return obj.clients.count()

    client_count.short_description = "Количество получателей"


@admin.register(Attempt)
class AttemptAdmin(admin.ModelAdmin):
    list_display = ("mailing", "timestamp", "status", "server_response_preview")
    list_filter = ("status", "timestamp")
    readonly_fields = ("timestamp", "status", "server_response", "mailing")

    def server_response_preview(self, obj):
        return (
            obj.server_response[:75] + "..."
            if obj.server_response and len(obj.server_response) > 75
            else obj.server_response or "—"
        )

    server_response_preview.short_description = "Ответ сервера"
