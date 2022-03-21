# language_dialog.py
#
# Copyright 2021 Andrey Maksimov
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE X CONSORTIUM BE LIABLE FOR ANY
# CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT,
# TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
# Except as contained in this notice, the name(s) of the above copyright
# holders shall not be used in advertising or otherwise to promote the sale,
# use or other dealings in this Software without prior written
# authorization.
from gettext import gettext as _

from gi.repository import Gtk, Granite, Handy

from .language_manager import language_manager


class LanguagePacksDialog(Handy.Window):
    downloaded_list = []

    def __init__(self, transient_for: Gtk.Window, **kwargs):
        super().__init__(transient_for=transient_for, **kwargs)

        self.resize(400, 450)
        self.set_modal(True)

        self.main_box: Gtk.Box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, vexpand=True)

        self.header_bar = Handy.HeaderBar()
        self.header_bar.set_title('Available Languages')
        self.header_bar.set_show_close_button(True)
        self.main_box.pack_start(self.header_bar, False, True, 0)
        # self.main_box.pack_start(header_label, False, True, 8)

        scrolled_view = Gtk.ScrolledWindow(vexpand=True)
        self.language_listbox = Gtk.ListBox()
        self.language_listbox.set_selection_mode(Gtk.SelectionMode.NONE)
        self.language_listbox.set_sort_func(self.sort_rows)

        self.reload_language_list()

        language_manager.connect('downloaded', lambda sender, code: self.reload_language_list())
        language_manager.connect('removed', lambda sender, code: self.reload_language_list())

        scrolled_view.add(self.language_listbox)
        self.main_box.pack_start(scrolled_view, True, True, 8)

        self.add(self.main_box)
        self.show_all()

    def reload_language_list(self):
        for child in self.language_listbox.get_children():
            self.language_listbox.remove(child)

        for lang_code in language_manager.get_available_codes():
            self.language_listbox.add(LanguageRow(lang_code))

        self.language_listbox.show_all()

    def sort_rows(self, row1: Gtk.ListBoxRow, row2: Gtk.ListBoxRow) -> int:
        """
        Used to sort languages list by its name not code.

        See https://lazka.github.io/pgi-docs/index.html#Gtk-3.0/callbacks.html#Gtk.ListBoxSortFunc for details.
        """
        lang_row1: LanguageRow = row1.get_child()
        lang_row2: LanguageRow = row2.get_child()
        lang1 = language_manager.get_language(lang_row1.lang_code)
        lang2 = language_manager.get_language(lang_row2.lang_code)

        if lang1 > lang2:
            return 1
        elif lang1 < lang2:
            return -1
        return 0


class LanguageRow(Gtk.Box):
    def __init__(self, lang_code, **kwargs):
        super().__init__(margin_top=8, margin_bottom=8, **kwargs)

        self.lang_code = lang_code
        self.set_size_request(-1, 34)

        self.label = Gtk.Label(_(language_manager.get_language(self.lang_code)), halign=Gtk.Align.START)

        self.download_widget: Gtk.Button = Gtk.Button()
        self.download_widget.connect('clicked', self.download_clicked)

        self.update_ui()
        self.set_margin_end(12)

    def update_ui(self):
        # Downloaded
        if self.lang_code in language_manager.get_downloaded_codes():
            self.download_widget.set_image(Gtk.Image.new_from_icon_name('user-trash-symbolic', Gtk.IconSize.BUTTON))
            self.download_widget.set_visible(True)
            self.get_style_context().add_class("downloaded")
        # In progress
        elif self.lang_code in language_manager.loading_languages:
            self.download_widget.set_sensitive(False)
            self.get_style_context().remove_class("downloaded")
        # Not yet
        else:
            self.get_style_context().remove_class("downloaded")
            self.download_widget.set_visible(True)
            self.download_widget.set_image(
                Gtk.Image.new_from_icon_name('folder-download-symbolic', Gtk.IconSize.BUTTON))

        self.pack_start(self.label, True, True, 8)
        self.pack_end(self.download_widget, False, True, 8)

    def download_clicked(self, widget) -> None:
        if self.lang_code in language_manager.loading_languages:
            return

        if self.lang_code in language_manager.get_downloaded_codes():
            language_manager.remove_language(self.lang_code)
            self.update_ui()
            return

        language_manager.download(self.lang_code)
        self.update_ui()
