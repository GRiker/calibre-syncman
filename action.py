#!/usr/bin/env python
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, Greg Riker <griker@hotmail.com>'
__docformat__ = 'restructuredtext en'

import  os

from calibre.gui2.actions import InterfaceAction
from calibre.utils.config import config_dir
from calibre.utils.zipfile import ZipFile

from calibre_plugins.syncman.common_utils import (
    CompileUI, Logger, set_plugin_icon_resources)

from calibre_plugins.syncman import SyncManPlugin

from PyQt4.Qt import QIcon

# The first icon is the plugin icon, referenced by position.
# The rest of the icons are referenced by name
PLUGIN_ICONS = ['images/disabled.png', 'images/enabled.png']

plugin_resources_path = os.path.join(config_dir, 'plugins', 'SyncMan_resources')

class SyncManAction(InterfaceAction, Logger):

    name = 'SyncMan'

    # Declare the main action associated with this plugin
    # The keyboard shortcut can be None if you dont want to use a keyboard
    # shortcut. Remember that currently calibre has no central management for
    # keyboard shortcuts, so try to use an unusual/unused shortcut.
    # action_spec = (text, icon_path, tooltip, keyboard shortcut)
    action_spec = ('SyncMan', None, 'Configure SyncMan', None)

    def apply_settings(self):
        # In an actual non trivial plugin, you would probably need to
        # do something based on the settings in prefs
        #from calibre_plugins.syncman.config import prefs
        #prefs
        self._log_location()

    def genesis(self):
        self._log_location("v{0}.{1}.{2}".format(*SyncManPlugin.version))
        from calibre_plugins.syncman.config import prefs

        self.prefs = prefs

        # Read the plugin icons and store for potential sharing with the config widget
        icon_resources = self.load_resources(PLUGIN_ICONS)
        set_plugin_icon_resources(self.name, icon_resources)


        self.resources_path = os.path.join(config_dir, 'plugins', "%s_resources" % self.name.replace(' ', '_'))
        if not os.path.exists(self.resources_path):
            os.makedirs(self.resources_path)

        # This method is called once per plugin, do initial setup here

        # Set the icon for this interface action
        # The get_icons function is a builtin function defined for all your
        # plugin code. It loads icons from the plugin zip file. It returns
        # QIcon objects, if you want the actual data, use the analogous
        # get_resources builtin function.
        #
        # Note that if you are loading more than one icon, for performance, you
        # should pass a list of names to get_icons. In this case, get_icons
        # will return a dictionary mapping names to QIcons. Names that
        # are not found in the zip file will result in null QIcons.

        if self.prefs.get('sync_app'):
            icon = get_icons('images/enabled.png')
        else:
            icon = QIcon(I('config.png'))


        # The qaction is automatically created from the action_spec defined
        # above

        self.qaction.setIcon(icon)
        self.qaction.triggered.connect(self.show_dialog)

        # Populate the help resources
        self.inflate_help_resources()

        # Populate icon resources
        self.inflate_icon_resources()

        # Populate the wizard resources
        self.inflate_wizard_resources()

    def inflate_help_resources(self):
        '''
        Extract the help resources from the plugin
        '''
        help_resources = []
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if (candidate.startswith('help/') and candidate.endswith('.html') or
                    candidate.startswith('help/images/')):
                    help_resources.append(candidate)

        rd = self.load_resources(help_resources)
        for resource in help_resources:
            if not resource in rd:
                continue
            fs = os.path.join(self.resources_path, resource)
            if os.path.isdir(fs) or fs.endswith('/'):
                continue
            if not os.path.exists(os.path.dirname(fs)):
                os.makedirs(os.path.dirname(fs))
            with open(fs, 'wb') as f:
                f.write(rd[resource])

    def inflate_icon_resources(self):
        '''
        Extract the icon resources from the plugin
        '''
        icons = []
        with ZipFile(self.plugin_path, 'r') as zf:
            for candidate in zf.namelist():
                if candidate.endswith('/'):
                    continue
                if candidate.startswith('icons/'):
                    icons.append(candidate)
        ir = self.load_resources(icons)
        for icon in icons:
            if not icon in ir:
                continue
            fs = os.path.join(self.resources_path, icon)
            if not os.path.exists(fs):
                if not os.path.exists(os.path.dirname(fs)):
                    os.makedirs(os.path.dirname(fs))
                with open(fs, 'wb') as f:
                    f.write(ir[icon])

    def inflate_wizard_resources(self):
        wr = 'sync_app_wizard.py'
        target = os.path.join(self.resources_path, wr)
        if os.path.exists(target):
            os.remove(target)

        with ZipFile(self.plugin_path, 'r') as zfr:
            try:
                zfr.extract(wr, self.resources_path)
            except:
                self._log_location()
                import traceback
                self._log(traceback.format_exc())
                raise Exception("Unable to inspect {}".format(wr))

    def initialization_complete(self):
        '''
        Initialization of main GUI is complete
        '''
        self._log_location()

    def show_dialog(self):
        '''
        Show the configuration dialog
        '''
        self._log_location()
        self.interface_action_base_plugin.do_user_config()

    def shutting_down(self):
        '''
        Main GUI shutting down
        '''
        self._log_location()

        return True