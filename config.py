#!/usr/bin/env python
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, Greg Riker <griker@hotmail.com>'
__docformat__ = 'restructuredtext en'

import importlib, os, sys

from PyQt4.Qt import QComboBox, QHBoxLayout, QIcon, QLabel, QLineEdit, QWidget

from calibre.constants import DEBUG
from calibre.gui2.dialogs.message_box import MessageBox
from calibre.gui2.ui import get_gui
from calibre.utils.config import config_dir, JSONConfig

from calibre_plugins.syncman.common_utils import Logger, compile_widgets

# Import Ui_Dialog from syncman.ui
if True:
    compile_widgets()
    widget_path = os.path.join(config_dir, 'plugins', 'SyncMan_resources')
    sys.path.insert(0, widget_path)
    from syncman_ui import Ui_Dialog
    sys.path.remove(widget_path)

prefs = JSONConfig('plugins/SyncMan')

class ConfigWidget(QWidget, Ui_Dialog, Logger):

    def __init__(self, plugin_action):
        QWidget.__init__(self)
        Ui_Dialog.__init__(self)
        self.setupUi(self)
        self.parent = plugin_action
        self.gui = get_gui()
        self.prefs = prefs
        self.resources_path = plugin_action.resources_path

        self._log_location()

        # Restore the debug settings
        self.debug_plugin.setChecked(self.prefs.get('debug_plugin', False))

        # Add the defined sync services to the combobox
        sync_app_list = self.prefs.get('sync_apps', {}).keys()
        self.sync_apps.blockSignals(True)
        self.sync_apps.addItems([''])
        self.sync_apps.addItems(sorted(sync_app_list, key=lambda s: s.lower()))
        self.sync_apps.setInsertPolicy(QComboBox.InsertAlphabetically)

        # Select the previously selected sync service
        selected_sync_app = self.prefs.get('sync_app', '')
        index = self.sync_apps.findText(selected_sync_app)
        self.sync_apps.setCurrentIndex(index)

        # Configure the tool buttons
        self.forget_tb.setIcon(QIcon(I('clear_left.png')))
        self.forget_tb.clicked.connect(self.forget_service)

        self.wizard_tb.setIcon(QIcon(I('wizard.png')))
        self.wizard_tb.clicked.connect(self.add_service)

        # Hook changes to the sync_apps combobox
        self.sync_apps.currentIndexChanged.connect(self.sync_apps_changed)
        self.sync_apps.blockSignals(False)
        self.sync_apps_changed()

    def add_service(self):
        '''
        Modeled after MXD:config:launch_cc_wizard()
        '''
        self._log_location()
        klass = os.path.join(self.resources_path, 'sync_app_wizard.py')
        if not os.path.exists(klass):
            self._log("Unable to load from '{}'".format(klass))
            return

        self._log("importing SyncApp Wizard dialog from '{}'".format(klass))
        sys.path.insert(0, self.resources_path)
        this_dc = importlib.import_module('sync_app_wizard')
        sys.path.remove(self.resources_path)
        dlg = this_dc.SyncAppWizard(self, verbose=DEBUG)
        if dlg.exec_():
            # Retrieve the selected sync_app
            sync_app_fs = str(dlg.sync_app_path_le.text())
            sync_app_name = str(dlg.app_name_le.text())

            # Update prefs with new sync app
            sync_apps = self.prefs.get('sync_apps', {})
            sync_apps[sync_app_name] = sync_app_fs
            self.prefs.set('sync_apps', sync_apps)

            # Add sync_app to combobox, select
            self.sync_apps.addItem(sync_app_name)
            index = self.sync_apps.findText(sync_app_name)
            self.sync_apps.setCurrentIndex(index)

    def forget_service(self):
        '''
        Remove the currently selected sync app
        '''
        self._log_location()

        key = str(self.sync_apps.currentText())

        title = "Forget syncing application".format(key)
        msg = ("<p>Forget '{}' syncing application?".format(key))
        dlg = MessageBox(MessageBox.QUESTION, title, msg,
                         parent=self.gui, show_copy_button=False)
        if dlg.exec_():
            # Delete key from prefs
            sync_apps = self.prefs.get('sync_apps', {})
            del sync_apps[key]
            self.prefs.set('sync_apps', sync_apps)

            # Remove from combobox
            index = self.sync_apps.currentIndex()
            self.sync_apps.removeItem(index)

    def save_settings(self):
        self._log_location()
        self.prefs.set('debug_plugin', self.debug_plugin.isChecked())
        self.prefs.set('sync_app', str(self.sync_apps.currentText()))

    def sync_apps_changed(self, *args):
        self._log_location(self.sync_apps.currentText())
        selected = str(self.sync_apps.currentText())
        if selected:
            self.forget_tb.setEnabled(True)
        else:
            self.forget_tb.setEnabled(False)


# For testing ConfigWidget, run from command line:
# cd ~/Documents/calibredev/SyncMan
# calibre-debug config.py 2> >(grep -v 'CoreAnimation\|CoreText\|modalSession' 1>&2)
# Search 'SyncMan'
if __name__ == '__main__':
    from PyQt4.Qt import QApplication
    from calibre.gui2.preferences import test_widget
    app = QApplication([])
    test_widget('Advanced', 'Plugins')


