#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import os
import re
from subprocess import Popen, PIPE

import gtk
import appindicator
from threading import Timer, Thread
import time

is_alive = True
selected_names = []

names = [
    "Aho Augasmägi",
    "Aivar Naaber",
    "Andrei Solntsev",
    "Anton Keks",
    "Erik Jõgi",
    "Erkki Teedla",
    "Jaan Sepp",
    "Jarmo Pertman",
    "Kirill Klenski",
    "Kunnar Klauks",
    "Kristjan Kokk",
    "Maksim Säkki",
    "Marko Randrüüt",
    "Marek Kusmin",
    "Patrick Abner",
    "Revo Sirel",
    "Tanel Tamm",
    "Tarmo Ojala",
    "Vadim Gerassimov",
    "Elina Matvejeva",
    "Annika Tammik",
    "Martin Beldman"
]


def add_name(menu, name):
    menu_item = gtk.CheckMenuItem(name)
    menu.append(menu_item)
    menu_item.connect("activate", name_selected)
    menu_item.show()


def name_selected(widget):
    name = widget.get_label()

    global selected_names
    if name in selected_names:
        selected_names.remove(name)
    else:
        selected_names.append(name)

    selected_emails = [re.sub(r" .*$", "@codeborne.com", name.lower()) for name in selected_names]

    git_username = ", ".join(selected_names)
    git_email = ", ".join(selected_emails)

    reset_git_username()
    os.system(u"git config --global user.name '%s'" % git_username)
    os.system(u"git config --global user.email '%s'" % git_email)
    ind.set_label(git_username)


def reset_git_username():
    os.system("git config --global --unset user.name")
    os.system("git config --global --unset user.email")
    ind.set_label('')


class UserReset(Thread):
    def reset_user_at_midnight(self):
        hour = datetime.now().hour
        if hour == 0:
            print "Reset git user at midnight %s" % datetime.now()
            reset_git_username()

    def run(self):
        while True:
            self.reset_user_at_midnight()
            time.sleep(60*55)


def run_jenkins_notifier():
    from jenkins_desktop_notify import JenkinsChecker
    jenkins_checker = JenkinsChecker()
    global is_alive
    while is_alive:
        jenkins_checker.check_jobs()
        jenkins_checker.sleep()


if __name__ == "__main__":
    current_name = Popen(["git", "config", "--global", "user.name"], stdout=PIPE).communicate()[0]
    current_name = current_name.strip()

    ind = appindicator.Indicator("git-indicator", "krb-valid-ticket", appindicator.CATEGORY_OTHER)
    ind.set_status(appindicator.STATUS_ACTIVE)
    ind.set_label(current_name)

    menu = gtk.Menu()

    for name in names:
        add_name(menu, name)

    ind.set_menu(menu)

    Timer(5, run_jenkins_notifier).start()

    UserReset().start()

    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
