#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import os
import re
from subprocess import Popen, PIPE

import gtk
import appindicator
from threading import Thread
import time
from gtk._gtk import CheckMenuItem

timer = None
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
    menu_item = CheckMenuItem(name)
    if is_selected(name):
        menu_item.set_active(True)

    menu.append(menu_item)
    menu_item.connect("activate", name_selected)
    menu_item.show()


def quit_program(widget):
    gtk.threads_leave()
    gtk.main_quit()


def add_action(menu, text, handler):
    menu_item = gtk.MenuItem(text)
    menu.append(menu_item)
    menu_item.connect("activate", handler)
    menu_item.show()


def is_selected(name):
    global selected_names
    return name in selected_names


def name_selected(widget):
    name = widget.get_label()

    global selected_names
    if is_selected(name):
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
    def __init__(self, menu):
        super(UserReset, self).__init__(name='UserReset')
        self.setDaemon(True)
        self.menu = menu

    def _uncheck_users_in_menu(self):
        for menu_item in self.menu.get_children():
            if isinstance(menu_item, CheckMenuItem):
                menu_item.set_active(False)

    def reset_user_at_midnight(self):
        self._uncheck_users_in_menu()
        hour = datetime.now().hour
        if hour == 0:
            print "Reset git user at midnight %s" % datetime.now()
            reset_git_username()
            self._uncheck_users_in_menu()

    def run(self):
        while True:
            self.reset_user_at_midnight()
            time.sleep(60*55)


class JenkinsNotifier(Thread):
    def __init__(self):
        super(JenkinsNotifier, self).__init__(name='JenkinsNotifier')
        self.setDaemon(True)

    def run(self):
        from jenkins_desktop_notify import JenkinsChecker
        JenkinsChecker().run()


if __name__ == "__main__":
    current_git_username = Popen(["git", "config", "--global", "user.name"], stdout=PIPE).communicate()[0]
    current_git_username = current_git_username.strip()
    selected_names = filter(None, [name.strip() for name in current_git_username.split(",")])

    ind = appindicator.Indicator("git-indicator", "krb-valid-ticket", appindicator.CATEGORY_OTHER)
    ind.set_status(appindicator.STATUS_ACTIVE)
    ind.set_label(current_git_username)

    menu = gtk.Menu()

    for name in names:
        add_name(menu, name)
    add_action(menu, 'exit', quit_program)

    ind.set_menu(menu)

    UserReset(menu).start()
    JenkinsNotifier().start()

    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
