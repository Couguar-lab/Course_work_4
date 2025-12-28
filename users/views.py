import logging

from django import forms
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.models import User
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.sites.shortcuts import get_current_site
from django.core.mail import send_mail
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.encoding import force_bytes, force_str
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.views.generic import CreateView, View

logger = logging.getLogger(__name__)


class RegisterView(CreateView):
    model = User
    template_name = "users/register.html"
    fields = ["username", "email"]
    success_url = reverse_lazy("users:login")

    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        form.fields["password1"] = forms.CharField(
            label="Пароль",
            widget=forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "Введите пароль"}
            ),
            min_length=8,
        )
        form.fields["password2"] = forms.CharField(
            label="Подтверждение пароля",
            widget=forms.PasswordInput(
                attrs={"class": "form-control", "placeholder": "Повторите пароль"}
            ),
        )
        form.fields["username"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Логин"}
        )
        form.fields["email"].widget.attrs.update(
            {"class": "form-control", "placeholder": "Email"}
        )
        return form

    def form_valid(self, form):
        password1 = form.cleaned_data.get("password1")
        password2 = form.cleaned_data.get("password2")
        if password1 != password2:
            form.add_error("password2", "Пароли не совпадают")
            return self.form_invalid(form)

        user = User.objects.create_user(
            username=form.cleaned_data["username"],
            email=form.cleaned_data["email"],
            password=password1,
            is_active=False,
        )

        # Lazy import модели
        ActivationToken = apps.get_model("mailing", "ActivationToken")
        ActivationToken.objects.create(user=user)

        # Обновляем user, чтобы reverse relation был доступен
        user.refresh_from_db()

        current_site = get_current_site(self.request)
        mail_subject = "Активация аккаунта — Сервис рассылок"
        message = render_to_string(
            "users/activation_email.html",
            {
                "user": user,
                "domain": current_site.domain,
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "token": user.activation_token.token,
            },
        )

        try:
            send_mail(
                subject=mail_subject,
                message=message,
                from_email="no-reply@yourdomain.com",
                recipient_list=[user.email],
                fail_silently=False,
            )
        except Exception as e:
            logger.error(f"Ошибка отправки письма активации: {e}")

        messages.success(
            self.request, "Регистрация прошла успешно! Проверьте почту для активации."
        )
        return redirect(self.success_url)


class ActivateAccount(View):
    def get(self, request, uidb64, token):
        print("Activation attempt. UID:", uidb64, "Token:", token)
        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            user = None

        if user is not None and user.is_active == False:
            ActivationToken = apps.get_model("mailing", "ActivationToken")
            try:
                activation_token = ActivationToken.objects.get(user=user)
                # Сравниваем строковые представления
                if str(activation_token.token) == token.strip():
                    user.is_active = True
                    user.save()
                    activation_token.delete()
                    messages.success(
                        request, "Аккаунт успешно активирован! Теперь вы можете войти."
                    )
                    return redirect("/")
            except ActivationToken.DoesNotExist:
                pass

        messages.error(
            request, "Ссылка активации недействительна или уже использована."
        )
        return redirect("users:login")


class UserLoginView(LoginView):
    template_name = "users/login.html"
    redirect_authenticated_user = True


class UserLogoutView(LogoutView):
    next_page = "users:login"
