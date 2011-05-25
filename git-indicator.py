import gobject
import gtk
import appindicator


def menuitem_response(w, buf):
 print buf

def new_developer(menu, name):
 menu_items = gtk.MenuItem(name)
 menu.append(menu_items)
 menu_items.show()

if __name__ == "__main__":
 ind = appindicator.Indicator ("example-simple-client",
                             "indicator-messages",
                             appindicator.CATEGORY_OTHER)
 ind.set_status (appindicator.STATUS_ACTIVE)
 #ind.set_attention_icon ("indicator-messages-new")
 ind.set_label("Anton Keks")

 # create a menu
 menu = gtk.Menu()

 # create some
 new_developer(menu, "Anton Keks")
 new_developer(menu, "Erik Jogi")
 new_developer(menu, "Revo Sirel")
 new_developer(menu, "Aivar Naaber")

 ind.set_menu(menu)

 gtk.main()
