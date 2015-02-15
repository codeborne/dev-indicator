#!/usr/bin/env python
# coding=utf-8
import base64

def cb_auth_header():
    temp = 'jenkins_viewer:Сколько у государства не воруй — все равно своего не вернешь!'
    return base64.encodestring(temp).replace('\n', '')
