#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import re
from subprocess import Popen, PIPE

import gtk
import appindicator
from threading import Timer, Thread
import time

names = [
     "Aho Augasmägi",
     "Aivar Naaber",
     "Andrei Solntsev",
     "Anton Keks",
     "Erik Jõgi",
     "Erkki Teedla",
     "Ingmar Oja",
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
#     "Aivo Vikat",
#     "Priidu Kull",
     "Martin Beldman"
#     "Karl Kesküla"
]


def add_name(menu, name):
    menu_item = gtk.MenuItem(name)
    menu.append(menu_item)
    menu_item.connect("activate", name_selected)
    menu_item.show()


def name_selected(widget):
    name = widget.get_label()
    os.system("git config --global user.name '" + name + "'")
    email = re.sub(r" .*$", "@codeborne.com", name.lower())
    os.system("git config --global user.email '" + email + "'")
    ind.set_label(name)


class UserReset(Thread):
    def run(self):
        while True:
            print "RESET user"
            time.sleep(20)

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

    from jenkins_desktop_notify import run_jenkins_notifier
    Timer(1, run_jenkins_notifier).start()

    UserReset().start()

    gtk.threads_init()
    gtk.threads_enter()
    gtk.main()
    gtk.threads_leave()
