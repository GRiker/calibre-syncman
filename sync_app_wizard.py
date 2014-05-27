#!/usr/bin/env python
# coding: utf-8

from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__ = 'GPL v3'
__copyright__ = '2014, Gregory Riker <griker@hotmail.com>'
__docformat__ = 'restructuredtext en'

import os, sys

from calibre.gui2.ui import get_gui

from calibre_plugins.syncman.action import plugin_resources_path
from calibre_plugins.syncman.common_utils import Logger

from PyQt4.Qt import (QDialog, QDialogButtonBox, QFileDialog, QIcon, QPixmap,
                      QSize)

# Import Ui_Form from form generated dynamically during initialization
if True:
    sys.path.insert(0, plugin_resources_path)
    from sync_app_wizard_ui import Ui_Dialog
    sys.path.remove(plugin_resources_path)


class SyncAppWizard(QDialog, Ui_Dialog, Logger):

    YELLOW_BG = '<font style="background:#FDFF99">{0}</font>'

    def __init__(self, parent, verbose=True):
        self._log_location()
        self.gui = get_gui()
        QDialog.__init__(self, self.gui)

        self.setupUi(self)
        self.verbose = verbose

        """
        # Populate the icon
        self.icon.setText('')
        self.icon.setMaximumSize(QSize(40, 40))
        self.icon.setScaledContents(True)
        self.icon.setPixmap(QPixmap(I('wizard.png')))

        self.populate_editor()

        self.highlight_step(1)
        """

        # Hook the buttonBox events
        self.bb.clicked.connect(self.dispatch_button_click)

        # Add the Accept button
        self.accept_button = self.bb.addButton(QDialogButtonBox.Ok)
        #self.accept_button.setIcon(QIcon(I('spell-check.png')))
        self.accept_button.setDefault(True)

        # Populate the browser toolbutton icon
        self.browser_tb.setIcon(QIcon(I('document_open.png')))
        self.browser_tb.clicked.connect(self.get_sync_app_fs)

        # Hook the sync_app edit controls
        self.sync_app_path_le.textChanged.connect(self.validate_sync_app)
        self.app_name_le.textChanged.connect(self.validate_sync_app)

        # Disable OK button until we have a valid app path and name
        self.validate_sync_app()


    def accept(self):
        self._log_location()
        super(SyncAppWizard, self).accept()

    def close(self):
        self._log_location()
        super(SyncAppWizard, self).close()

    def dispatch_button_click(self, button):
        '''
        BUTTON_ROLES = ['AcceptRole', 'RejectRole', 'DestructiveRole', 'ActionRole',
                        'HelpRole', 'YesRole', 'NoRole', 'ApplyRole', 'ResetRole']
        '''
        self._log_location()
        if self.bb.buttonRole(button) == QDialogButtonBox.AcceptRole:
            self.accept()

        elif self.bb.buttonRole(button) == QDialogButtonBox.RejectRole:
            self.close()

    def esc(self, *args):
        self.close()

    def get_sync_app_fs(self):
        '''
        Get path to selected sync_app
        '''
        self._log_location()
        sync_app = unicode(QFileDialog.getOpenFileName(
            self.gui,
            "Select sync app",
            os.path.expanduser("~"),
            "*.app").toUtf8())
        if sync_app:
            # Populate the filespec edit control
            self._log(sync_app)
            self.sync_app_path_le.setText(sync_app)

            # Populate the putative app name
            app_name = os.path.basename(sync_app)
            root_name = app_name.split('.')[0]
            self.app_name_le.setText(root_name)

    def highlight_step(self, step):
        '''
        '''
        self._log_location(step)
        if step == 1:
            #self.step_1.setText(self.YELLOW_BG.format(self.STEP_ONE.format(self.column_type)))
            self.step_1.setText(self.STEP_ONE.format(self.column_type))

    def validate_sync_app(self, *args):
        '''
        Confirm length of sync_app name > 0 and app is a valid file
        '''
        app_exists = os.path.exists(str(self.sync_app_path_le.text()))
        app_name = self.app_name_le.text()
        enabled = app_exists and len(app_name)
        self.accept_button.setEnabled(enabled)
