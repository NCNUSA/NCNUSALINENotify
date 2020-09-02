from django.db import models
from django.contrib.auth.models import User
from django.contrib import admin
import requests


class BroadcastGroup(models.Model):
    name = models.CharField(max_length=20, verbose_name="群組名")

    class Meta:
        verbose_name, verbose_name_plural = '推播群組', '推播群組'

    def __str__(self):
        return self.name


class Message(models.Model):
    user = models.ForeignKey(User,
                             on_delete=models.CASCADE, verbose_name='推播者'
                             )
    toGroup = models.CharField(max_length=20, verbose_name="推播至", default="全部")
    message = models.TextField(verbose_name="推播內容")
    title = models.CharField(verbose_name="標題", max_length=20)
    created_at = models.DateTimeField(verbose_name="發送日期", auto_now=True)

    class Meta:
        verbose_name, verbose_name_plural = '歷史紀錄', '歷史紀錄'

    def username(self):
        return self.user.username

    def __str__(self):
        return self.title
    username.short_description = "發送者"


class AccessToken(models.Model):
    token = models.TextField()
    groups = models.ManyToManyField(BroadcastGroup, verbose_name='群組')

    class Meta:
        verbose_name, verbose_name_plural = '推播用戶', '推播用戶'

    def username(self):
        url = "https://notify-api.line.me/api/status"
        headers = {
            "Authorization": "Bearer " + self.token,
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()["target"]
        else:
            return None

    def userType(self):
        url = "https://notify-api.line.me/api/status"
        headers = {
            "Authorization": "Bearer " + self.token,
        }
        r = requests.get(url, headers=headers)
        if r.status_code == 200:
            return r.json()["targetType"]
        else:
            return None
    userType.short_description = "種類"
    username.short_description = "用戶名"


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['title', 'username', "toGroup", "created_at"]
    search_fields = ("message", "title")

    def has_change_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AccessToken)
class AccessTokenAdmin(admin.ModelAdmin):
    list_display = ["username", "userType"]
    readonly_fields = ('token',)

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request, obj=None):
        return False


@admin.register(BroadcastGroup)
class BroadcastGroupAdmin(admin.ModelAdmin):
    list_display = ["name"]
