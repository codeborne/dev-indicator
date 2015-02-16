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
from hours import HoursReporter

names = [
    "Aho Augasmägi",
    "Aivar Naaber",
    "Andrei Solntsev",
    "Annika Tammik",
    "Anton Keks",
    "Dmitri Ess",
    "Dmitri Troškov",
    "Elina Matvejeva",
    "Erik Jõgi",
    "Erkki Teedla",
    "Jaan Sepp",
    "Jarmo Pertman",
    "Kirill Klenski",
    "Kunnar Klauks",
    "Kristjan Kokk",
    "Kätlin Hein",
    "Maksim Säkki",
    "Marek Kusmin",
    "Martin Beldman",
    "Nikita Abramenkov",
    "Patrick Abner",
    "Revo Sirel",
    "Sven Eller",
    "Tanel Tamm",
    "Tarmo Ojala",
    "Vadim Gerassimov",
    "Openway"
]

class Indicator:
    selected_names = []
    select_time = None
    ind = None

    def __init__(self):
        self.current_git_username = Popen(["git", "config", "--global", "user.name"], stdout=PIPE).communicate()[0].strip()
        self.selected_names = filter(None, [name.strip() for name in self.current_git_username.split(",")])

    def is_selected(self, name):
        return name in self.selected_names

    def add(self, name):
        self.selected_names.append(name)
        self.select_time = datetime.now()

    def remove(self, name):
        self.selected_names.remove(name)

    def reset_git_username(self):
        os.system("git config --global --unset user.name")
        os.system("git config --global --unset user.email")
        indicator.ind.set_label('')

    def name_selected(self, widget):
        name = widget.get_label()

        if self.is_selected(name):
            self.remove(name)
        else:
            self.add(name)

        self.selected_emails = [re.sub(r" .*$", "@codeborne.com", name.lower()) for name in self.selected_names]

        git_username = ", ".join(self.selected_names)
        git_email = ", ".join(self.selected_emails)

        self.reset_git_username()
        os.system(u"git config --global user.name '%s'" % git_username)
        os.system(u"git config --global user.email '%s'" % git_email)
        self.ind.set_label(git_username)

    def _add_name_item(self, menu, name):
        menu_item = CheckMenuItem(name)
        if indicator.is_selected(name):
            menu_item.set_active(True)

        menu.append(menu_item)
        menu_item.connect("activate", self.name_selected)

    def _add_action_item(self, menu, text, handler):
        menu_item = gtk.MenuItem(text)
        menu.append(menu_item)
        menu_item.connect("activate", handler)

    def quit(self, widget=None):
        gtk.threads_leave()
        gtk.main_quit()

    def restart(self, widget=None):
        print "Restarting"
        os.execl(__file__, __file__)

    def build_menu(self):
        self.ind = appindicator.Indicator("git-indicator", "krb-valid-ticket", appindicator.CATEGORY_OTHER)
        self.ind.set_status(appindicator.STATUS_ACTIVE)
        self.ind.set_label(self.current_git_username)

        menu = gtk.Menu()

        for name in names: self._add_name_item(menu, name)

        separator = SeparatorMenuItem()
        menu.append(separator)

        self._add_action_item(menu, 'Restart', self.restart)
        self._add_action_item(menu, 'Quit', self.quit)
        menu.show_all()

        self.ind.set_menu(menu)

indicator = Indicator()

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
            indicator.reset_git_username()
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
        updates = Popen(["git", "pull"], cwd=os.path.dirname(os.path.realpath(__file__)), stdout=PIPE, stderr=STDOUT).communicate()[0]

        if updates:
            if 'Aborting' in updates:
                raise Exception(updates)
            elif 'Already up-to-date' not in updates:
                print 'Updates found: %s' % updates
                indicator.restart()

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
        self.jenkins_checker.run()


if __name__ == "__main__":
    indicator.build_menu()

    #AutoUpdate().start()
    #UserReset(menu).start()
    #HoursReporter().start()

    #jenkins_checker = JenkinsChecker()
    #JenkinsNotifier(jenkins_checker).start()

    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
