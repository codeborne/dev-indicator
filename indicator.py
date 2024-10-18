from datetime import datetime
import os
import re
from subprocess import Popen, PIPE, STDOUT
from threading import Thread
import time

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('AyatanaAppIndicator3', '0.1')

from gi.repository import Gtk as gtk, AyatanaAppIndicator3 as appindicator

from extras.jenkins_desktop_notify import JenkinsChecker, JenkinsNotifier
#from autoupdate import AutoUpdate
#from extras.hours import HoursReporter

class Indicator:
    devs = {}
    selected_names = []
    selected_emails = []
    select_time = None
    ind = None
    menu = None

    def __init__(self):
        self.load_devs()
        current_git_username = Popen(["git", "config", "--global", "user.name"], stdout=PIPE).communicate()[0].decode('utf-8').strip()
        self.selected_names = list(filter(lambda name: name in self.devs, [name.strip() for name in current_git_username.split(",")]))
        self.menu = self.build_menu(current_git_username)

    def load_devs(self):
        with open("developers.txt") as f:
            for line in f:
                name, email = line.partition(":")[::2]
                self.devs[name.strip()] = email.strip()

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
        self.ind.set_label('', '')

    def name_selected(self, widget):
        name = widget.get_label()

        if self.is_selected(name):
            self.remove(name)
        else:
            self.add(name)

        self.selected_emails = [self.devs[name] for name in self.selected_names]

        git_username = ", ".join(self.selected_names)
        git_email = ", ".join(self.selected_emails)

        self.reset_git_username()
        os.system("git config --global user.name '%s'" % git_username)
        os.system("git config --global user.email '%s'" % git_email)
        self.ind.set_label(git_username, git_username)

    def _add_name_item(self, menu, name):
        menu_item = gtk.CheckMenuItem.new_with_label(name)
        if self.is_selected(name):
            menu_item.set_active(True)
        menu.append(menu_item)
        menu_item.connect("activate", self.name_selected)

    def _add_action_item(self, menu, text, handler):
        menu_item = gtk.MenuItem.new_with_label(text)
        menu.append(menu_item)
        menu_item.connect("activate", handler)

    def quit(self, widget=None):
        gtk.main_quit()

    def restart(self, widget=None):
        print("Restarting")
        os.execl(__file__, __file__)

    def build_menu(self, current_git_username):
        self.ind = appindicator.Indicator.new("git-indicator", "krb-valid-ticket", appindicator.IndicatorCategory.APPLICATION_STATUS)
        self.ind.set_status(appindicator.IndicatorStatus.ACTIVE)
        self.ind.set_label(current_git_username, current_git_username)

        menu = gtk.Menu()

        for name in sorted(self.devs): self._add_name_item(menu, name)

        separator = gtk.SeparatorMenuItem()
        menu.append(separator)

        self._add_action_item(menu, 'Restart', self.restart)
        self._add_action_item(menu, 'Quit', self.quit)
        menu.show_all()

        self.ind.set_menu(menu)
        return menu

    def uncheck_all_names(self):
        for menu_item in self.menu.get_children():
            if isinstance(menu_item, gtk.CheckMenuItem):
                menu_item.set_active(False)


class UserReset(Thread):
    def __init__(self, indicator):
        super(UserReset, self).__init__(name='UserReset')
        self.setDaemon(True)
        self.indicator = indicator

    def reset_user_at_midnight(self):
        hour = datetime.now().hour
        if hour == 0:
            print("Reset git user at midnight %s" % datetime.now())
            self.indicator.reset_git_username()
            self.indicator.uncheck_all_names()

    def run(self):
        while True:
            self.reset_user_at_midnight()
            time.sleep(60*55)

if __name__ == "__main__":
    indicator = Indicator()
    UserReset(indicator).start()

    #AutoUpdate(indicator).start()
    #HoursReporter(indicator).start()
    JenkinsNotifier(JenkinsChecker()).start()

    gtk.main()
