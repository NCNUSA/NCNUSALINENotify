from django.shortcuts import render
from django.views import View
from django.http import HttpResponseRedirect
from django.http import HttpResponseForbidden
import requests
from NCNUSALineNotify import settings
from .models import Message, AccessToken, BroadcastGroup
import logging

logger = logging.getLogger(__name__)


def lineNotifyMessage(token, msg):
    headers = {
        "Authorization": "Bearer " + token,
        "Content-Type": "application/x-www-form-urlencoded"
    }
    payload = {'message': msg}
    r = requests.post("https://notify-api.line.me/api/notify",
                      headers=headers, params=payload
                      )
    return r


def index(request):
    if request.session.get('registered', False):
        return render(request, "register.html")
    return render(request, "register.html", {
        "id": settings.LINE_CLIENT,
        "url": settings.HOST+"/register",
    })


def register(request):
    if not request.GET.get("code", False):
        return HttpResponseForbidden("Not for you")
    payload, url = {
        "grant_type": "authorization_code",
        "code": request.GET.get("code"),
        "redirect_uri": settings.HOST+"/register",
        "client_id": settings.LINE_CLIENT,
        "client_secret": settings.LINE_CLIENT_KEY
    }, "https://notify-bot.line.me/oauth/token"
    r = requests.post(url, params=payload)
    if r.status_code == 200:
        AccessToken(token=r.json()["access_token"]).save()
        request.session["registered"] = True
    else:
        return HttpResponseForbidden("Fail")
    return HttpResponseRedirect("/")


class Send(View):
    def send_pro(self, content, tokens):
        for token in tokens:
            status = lineNotifyMessage(token.token, content)
            if status.status_code == 401:
                token.delete()
            elif status.status_code != 200:
                return status
        return None

    groupsOptions = [{'name': '全部', 'id': -1}]
    for x in BroadcastGroup.objects.all():
        groupsOptions.append({'name': x.name, 'id': x.id})

    def get(self, request):
        if not request.user.is_authenticated:  # 未登入
            return HttpResponseRedirect('/admin/login/?next=/pushMessage')
        return render(request, "index.html", {
            "groups": self.groupsOptions
        })

    def post(self, request):
        if not request.user.is_authenticated:  # 未登入
            return HttpResponseForbidden('想幹嘛')
        title = request.POST.get("title")
        content = request.POST.get("content")
        groups = request.POST.getlist("groups")
        if title is None or content is None or len(groups) == 0:
            return render(request, "index.html", {
                "title": title,
                "content": content,
                "message": "未填寫完成",
                "groups": self.groupsOptions
            })
        if len(title) > 20:
            return render(request, "index.html", {
                "title": title,
                "content": content,
                "message": "標題長度不要超過20",
                "groups": self.groupsOptions
            })
        for group in groups:
            if int(group) == -1:
                tokens = AccessToken.objects.all()
                status = self.send_pro(content, tokens)
                if status is not None:
                    logger.error(status)
                    return render(request, "index.html", {
                        "title": title,
                        "content": content,
                        "message": "推播發送失敗",
                        "groups": self.groupsOptions
                    })
            else:
                tokens = AccessToken.objects.filter(groups=int(group))
                status = self.send_pro(content, tokens)
                if status is not None:
                    logger.error(status)
                    return render(request, "index.html", {
                        "title": title,
                        "content": content,
                        "message": "推播發送失敗",
                        "groups": self.groupsOptions
                    })
            Message(
                user=request.user,
                message=content,
                toGroup=BroadcastGroup.objects.get(id=group).name,
                title=title
            ).save()
        return render(request, "index.html", {
                "title": title,
                "content": content,
                "message": "推播發送成功",
                "groups": self.groupsOptions
        })
