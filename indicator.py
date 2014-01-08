#!/usr/bin/python
# -*- coding: utf-8 -*-
from datetime import datetime
import os
import re
from subprocess import Popen, PIPE, STDOUT

import gtk
import appindicator
from threading import Thread
import time
from gtk._gtk import CheckMenuItem, SeparatorMenuItem
from jenkins_desktop_notify import JenkinsChecker

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


def quit_program(widget):
    gtk.threads_leave()
    gtk.main_quit()


def add_action(menu, text, handler):
    menu_item = gtk.MenuItem(text)
    menu.append(menu_item)
    menu_item.connect("activate", handler)


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
        hour = datetime.now().hour
        if hour == 0:
            print "Reset git user at midnight %s" % datetime.now()
            reset_git_username()
            self._uncheck_users_in_menu()

    def run(self):
        while True:
            self.reset_user_at_midnight()
            time.sleep(60*55)


class AutoUpdate(Thread):
    def __init__(self):
        super(AutoUpdate, self).__init__(name='AutoUpdate')
        self.setDaemon(True)

    def _check_for_updates(self):
        print "Check for updates..."
        updates = Popen(["git", "pull"], stdout=PIPE, stderr=STDOUT).communicate()[0]

        if updates:
            if 'Aborting' in updates:
                raise Exception(updates)
            elif 'Already up-to-date' not in updates:
                print 'Updates found: %s' % updates
                print "Restarting"
                os.execl(__file__, __file__)

    def run(self):
        while True:
            try:
                self._check_for_updates()
                time.sleep(60*5)
            except Exception as e:
                print 'Failed to update: %s' % e
                time.sleep(60*60)


class JenkinsNotifier(Thread):
    def __init__(self, jenkins_checker):
        super(JenkinsNotifier, self).__init__(name='JenkinsNotifier')
        self.setDaemon(True)
        self.jenkins_checker = jenkins_checker

    def run(self):
        jenkins_checker.run()


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

    separator = SeparatorMenuItem()
    menu.append(separator)

    add_action(menu, 'Quit', quit_program)
    menu.show_all()

    ind.set_menu(menu)

    AutoUpdate().start()
    UserReset(menu).start()

    jenkins_checker = JenkinsChecker()
    JenkinsNotifier(jenkins_checker).start()

    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
