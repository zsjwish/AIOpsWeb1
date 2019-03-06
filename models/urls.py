#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# @Time    : 2019/1/23 11:05
# @Author  : zsj
# @File    : urls.py
# @Description:
from django.conf.urls import url

from models import views

app_name = 'models'
print("urlssssss")
urlpatterns = [
    url(r'^index/$', views.index, name = 'index'),
    url(r'^upload/$', views.upload, name = 'upload'),
    url(r'^success/$', views.success, name = 'success'),
    url(r'^menu/$', views.menu, name = 'menu'),
    url(r'^train/$', views.train, name = 'train'),
    url(r'^hello/$', views.hello, name = 'hello'),
    url(r'^submit/$', views.submit, name = 'submit'),
    url(r'^tag/$', views.tag, name = 'tag'),
    url(r'^predict/$', views.predict, name = 'predict'),
    url(r'^model_info/$', views.model_info, name = 'model_info'),
    url(r'^dashboard/$', views.dashboard),
]
