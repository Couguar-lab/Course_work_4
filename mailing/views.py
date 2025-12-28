import logging

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_control, cache_page
from django.views.generic import (
    CreateView,
    DeleteView,
    DetailView,
    ListView,
    TemplateView,
    UpdateView,
    View,
)

from .forms import ClientForm, MailingForm, MessageForm
from .models import Attempt, Client, Mailing, Message
from .permissions import ManagerRequiredMixin

logger = logging.getLogger("mailing")


@method_decorator(cache_page(300), name="dispatch")
@method_decorator(cache_control(max_age=300, private=True), name="dispatch")
class HomeView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.user.is_authenticated:
            context["total_mailings"] = Mailing.objects.filter(
                owner=self.request.user
            ).count()
            context["active_mailings"] = Mailing.objects.filter(
                owner=self.request.user, status="launched"
            ).count()
            context["unique_clients"] = (
                Client.objects.filter(owner=self.request.user).distinct().count()
            )
        else:
            context["total_mailings"] = 0
            context["active_mailings"] = 0
            context["unique_clients"] = 0
        return context


def send_mailing_now(mailing):
    """
    Отправляет сообщения по рассылке прямо сейчас.
    Создаёт записи Attempt для каждой попытки.
    Обновляет статус рассылки.
    """
    logger.info(
        f"Запуск отправки рассылки ID={mailing.id} «{mailing.message.subject}» владельца {mailing.owner}"
    )

    if mailing.status == "completed":
        logger.warning(f"Попытка отправить завершённую рассылку ID={mailing.id}")
        return

    # Обновляем статус на 'Запущена', если ещё не запущена
    if mailing.status == "created":
        mailing.status = "launched"
        mailing.save(update_fields=["status"])

    # Проверяем, не прошло ли время окончания
    if timezone.now() > mailing.end_time:
        mailing.status = "completed"
        mailing.save(update_fields=["status"])
        return

    subject = mailing.message.subject
    body = mailing.message.body
    from_email = (
        settings.EMAIL_HOST_USER
        if hasattr(settings, "EMAIL_HOST_USER")
        else "no-reply@example.com"
    )

    recipients = [client.email for client in mailing.clients.all()]

    for email in recipients:
        attempt = Attempt.objects.create(
            mailing=mailing, status="failure", server_response=""
        )
        try:
            send_mail(
                subject=subject,
                message=body,
                from_email=from_email,
                recipient_list=[email],
                fail_silently=False,
            )
            attempt.status = "success"
            attempt.server_response = "OK"
            logger.info(f"Успешно отправлено на {email} (рассылка ID={mailing.id})")
        except Exception as e:
            attempt.server_response = str(e)
            logger.error(f"Ошибка отправки на {email} (рассылка ID={mailing.id}): {e}")
        finally:
            attempt.save()

    logger.info(f"Отправка рассылки ID={mailing.id} завершена")


# === КЛИЕНТЫ ===
@method_decorator(cache_page(180), name="dispatch")
class ClientListView(LoginRequiredMixin, ListView):
    model = Client
    template_name = "mailing/client_list.html"
    context_object_name = "clients"
    paginate_by = 10

    def get_queryset(self):
        return Client.objects.filter(owner=self.request.user)


class ClientDetailView(LoginRequiredMixin, DetailView):
    model = Client
    template_name = "mailing/client_detail.html"


class ClientCreateView(LoginRequiredMixin, CreateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class ClientUpdateView(LoginRequiredMixin, UpdateView):
    model = Client
    form_class = ClientForm
    template_name = "mailing/client_form.html"
    success_url = reverse_lazy("mailing:client_list")


class ClientDeleteView(LoginRequiredMixin, DeleteView):
    model = Client
    template_name = "mailing/client_confirm_delete.html"
    success_url = reverse_lazy("mailing:client_list")


# === СООБЩЕНИЯ ===
@method_decorator(cache_page(180), name="dispatch")
class MessageListView(LoginRequiredMixin, ListView):
    model = Message
    template_name = "mailing/message_list.html"
    context_object_name = "messages"
    paginate_by = 10

    def get_queryset(self):
        return Message.objects.filter(owner=self.request.user)


class MessageDetailView(LoginRequiredMixin, DetailView):
    model = Message
    template_name = "mailing/message_detail.html"


class MessageCreateView(LoginRequiredMixin, CreateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MessageUpdateView(LoginRequiredMixin, UpdateView):
    model = Message
    form_class = MessageForm
    template_name = "mailing/message_form.html"
    success_url = reverse_lazy("mailing:message_list")


class MessageDeleteView(LoginRequiredMixin, DeleteView):
    model = Message
    template_name = "mailing/message_confirm_delete.html"
    success_url = reverse_lazy("mailing:message_list")


# === РАССЫЛКИ ===
@method_decorator(cache_page(180), name="dispatch")
class MailingListView(LoginRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10

    def get_queryset(self):
        return Mailing.objects.filter(owner=self.request.user)


@method_decorator(cache_page(600), name="dispatch")
class MailingDetailView(LoginRequiredMixin, DetailView):
    model = Mailing
    template_name = "mailing/mailing_detail.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["attempts"] = self.object.attempts.all()
        return context


class MailingCreateView(LoginRequiredMixin, CreateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")

    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class MailingUpdateView(LoginRequiredMixin, UpdateView):
    model = Mailing
    form_class = MailingForm
    template_name = "mailing/mailing_form.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingDeleteView(LoginRequiredMixin, DeleteView):
    model = Mailing
    template_name = "mailing/mailing_confirm_delete.html"
    success_url = reverse_lazy("mailing:mailing_list")


class MailingSendNowView(LoginRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        logger.info(f"Ручной запуск рассылки ID={pk} пользователем {request.user}")

        if mailing.status == "completed":
            messages.error(
                request, "Рассылка уже завершена и не может быть отправлена."
            )
        elif timezone.now() < mailing.start_time:
            messages.warning(
                request,
                "Рассылка ещё не началась (время первой отправки не наступило).",
            )
        else:
            send_mailing_now(mailing)
            messages.success(
                request,
                f'Рассылка "{mailing.message.subject}" запущена! Письма отправляются...',
            )

        return redirect("mailing:mailing_detail", pk=pk)


# Список всех пользователей (только для менеджеров)
class UserListView(ManagerRequiredMixin, ListView):
    model = User
    template_name = "mailing/manager/user_list.html"
    context_object_name = "users"
    paginate_by = 15

    def get_queryset(self):
        return User.objects.all().order_by("username")


# Блокировка/разблокировка пользователя
class UserToggleActiveView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        user = get_object_or_404(User, pk=pk)
        if user.is_superuser:
            messages.error(request, "Нельзя блокировать суперпользователя.")
        else:
            user.is_active = not user.is_active
            user.save()
            status = "заблокирован" if not user.is_active else "разблокирован"
            messages.success(request, f"Пользователь {user.username} {status}.")
        return redirect("mailing:manager_user_list")


# Просмотр всех рассылок (для менеджеров)
@method_decorator(cache_page(60), name="dispatch")
class AllMailingListView(ManagerRequiredMixin, ListView):
    model = Mailing
    template_name = "mailing/manager/all_mailing_list.html"
    context_object_name = "mailings"
    paginate_by = 10

    def get_queryset(self):
        return Mailing.objects.select_related("message", "owner").all()


# Отключение рассылки
class MailingDisableView(ManagerRequiredMixin, View):
    def post(self, request, pk):
        mailing = get_object_or_404(Mailing, pk=pk)
        mailing.status = "completed"
        mailing.save()
        messages.success(request, f'Рассылка "{mailing.message.subject}" отключена.')
        return redirect("mailing:manager_all_mailings")
