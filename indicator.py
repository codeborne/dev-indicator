# -*- coding: utf-8 -*-
import os
import re
from subprocess import Popen, PIPE

import gtk
import appindicator

names = [
     "Aho Augasmägi",
     "Aivar Naaber",
     "Alvar Lumberg",
     "Andrei Solntsev",
     "Anton Keks",
     "Erik Jõgi",
     "Erkki Teedla",
     "Ingmar Oja",
     "Jaan Sepp",
     "Jarmo Pertman",
     "Kirill Klenski",
     "Kunnar Klauks",
     "Maksim Säkki",
     "Marko Randrüüt",
     "Marek Kusmin",
     "Patrick Abner",
     "Revo Sirel",
     "Tanel Tamm",
     "Tarmo Ojala",
     "Vadim Gerassimov"
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

if __name__ == "__main__":
    current_name = Popen(["git", "config", "--global", "user.name"], stdout=PIPE).communicate()[0]
    current_name = current_name.strip()

    ind = appindicator.Indicator ("git-indicator", "krb-valid-ticket", appindicator.CATEGORY_OTHER)
    ind.set_status (appindicator.STATUS_ACTIVE)
    ind.set_label(current_name)

    menu = gtk.Menu()

    for name in names:
        add_name(menu, name)

    ind.set_menu(menu)

    gtk.main()
