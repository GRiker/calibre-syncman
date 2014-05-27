#!/usr/bin/env python
from __future__ import (unicode_literals, division, absolute_import,
                        print_function)

__license__   = 'GPL v3'
__copyright__ = '2014, Greg Riker <griker@hotmail.com>'
__docformat__ = 'restructuredtext en'

import cStringIO, os, re, sys, time
from datetime import datetime

from calibre.constants import DEBUG
from calibre.devices.usbms.driver import debug_print
from calibre.ebooks.BeautifulSoup import BeautifulStoneSoup
from calibre.utils.config import config_dir
from calibre.utils.zipfile import ZipFile

from PyQt4.uic import compileUi

class CompileUI(object):
    '''
    Compile Qt Creator .ui files at runtime
    '''
    def __init__(self, resources_path):
        self.resources_path = resources_path
        self.compiled_forms = {}
        self.help_file = None
        self.compiled_forms = self.compile_ui()

    def compile_ui(self):
        pat = re.compile(r'''(['"]):/images/([^'"]+)\1''')

        def sub(match):
            ans = 'I(%s%s%s)' % (match.group(1), match.group(2), match.group(1))
            return ans

        # >>> Entry point

        compiled_forms = {}
        self._find_forms()

        # Cribbed from gui2.__init__:build_forms()
        for form in self.forms:
            with open(form) as form_file:
                soup = BeautifulStoneSoup(form_file.read())
                property = soup.find('property', attrs={'name': 'windowTitle'})
                string = property.find('string')
                window_title = string.renderContents()

            compiled_form = self._form_to_compiled_form(form)
            if (not os.path.exists(compiled_form) or
                    os.stat(form).st_mtime > os.stat(compiled_form).st_mtime):

                if not os.path.exists(compiled_form):
                    if DEBUG:
                        debug_print(' compiling {}'.format(form))
                else:
                    if DEBUG:
                        debug_print(' recompiling {}'.format(form))
                    os.remove(compiled_form)
                buf = cStringIO.StringIO()
                compileUi(form, buf)
                dat = buf.getvalue()
                dat = dat.replace('__appname__', 'calibre')
                dat = dat.replace('import images_rc', '')
                dat = re.compile(r'(?:QtGui.QApplication.translate|(?<!def )_translate)\(.+?,\s+"(.+?)(?<!\\)",.+?\)').sub(r'_("\1")', dat)
                dat = dat.replace('_("MMM yyyy")', '"MMM yyyy"')
                dat = pat.sub(sub, dat)
                with open(compiled_form, 'wb') as cf:
                    cf.write(dat)

            compiled_forms[window_title] = compiled_form.rpartition(os.sep)[2].partition('.')[0]
            os.remove(form)
        return compiled_forms

    def _find_forms(self):
        forms = []
        for root, _, files in os.walk(self.resources_path):
            for name in files:
                if name.endswith('.ui'):
                    forms.append(os.path.abspath(os.path.join(root, name)))
        self.forms = forms

    def _form_to_compiled_form(self, form):
        compiled_form = form.rpartition('.')[0]+'_ui.py'
        return compiled_form


class Logger():
    '''
    A self-modifying class to print debug statements.
    If disabled in prefs, methods are neutered at first call for performance optimization
    '''
    LOCATION_TEMPLATE = "{cls}:{func}({arg1}) {arg2}"

    def _log(self, msg=None):
        '''
        Upon first call, switch to appropriate method
        '''
        from calibre_plugins.marvin_manager.config import plugin_prefs
        if not plugin_prefs.get('debug_plugin', False):
            # Neuter the method
            self._log = self.__null
            self._log_location = self.__null
        else:
            # Log the message, then switch to real method
            if msg:
                debug_print(" {0}".format(str(msg)))
            else:
                debug_print()

            self._log = self.__log
            self._log_location = self.__log_location

    def __log(self, msg=None):
        '''
        The real method
        '''
        if msg:
            debug_print(" {0}".format(str(msg)))
        else:
            debug_print()

    def _log_location(self, *args):
        '''
        Upon first call, switch to appropriate method
        '''
        from calibre_plugins.syncman.config import prefs
        if not prefs.get('debug_plugin', False):
            # Neuter the method
            self._log = self.__null
            self._log_location = self.__null
        else:
            # Log the message from here so stack trace is valid
            arg1 = arg2 = ''

            if len(args) > 0:
                arg1 = str(args[0])
            if len(args) > 1:
                arg2 = str(args[1])

            debug_print(self.LOCATION_TEMPLATE.format(cls=self.__class__.__name__,
                        func=sys._getframe(1).f_code.co_name,
                        arg1=arg1, arg2=arg2))

            # Switch to real method
            self._log = self.__log
            self._log_location = self.__log_location

    def __log_location(self, *args):
        '''
        The real method
        '''
        arg1 = arg2 = ''

        if len(args) > 0:
            arg1 = str(args[0])
        if len(args) > 1:
            arg2 = str(args[1])

        debug_print(self.LOCATION_TEMPLATE.format(cls=self.__class__.__name__,
                    func=sys._getframe(1).f_code.co_name,
                    arg1=arg1, arg2=arg2))

    def __null(self, *args, **kwargs):
        '''
        Optimized method when logger is silent
        '''
        pass


def compile_widgets():
    '''
    Compile widgets as needed
    '''
    plugin_path = os.path.join(config_dir, 'plugins', 'SyncMan.zip')
    resources_path = os.path.join(config_dir, 'plugins', 'SyncMan_resources')
    widgets = ['syncman', 'sync_app_wizard']

    with ZipFile(plugin_path, 'r') as zfr:
        try:
            for widget in widgets:
                needs_compilation = True

                # Get the .ui source timestamp
                ui_ts = zfr.getinfo(widget + '.ui').date_time
                ui_time = datetime(*ui_ts).timetuple()

                # Do we have a compiled version with a later timestamp?
                compiled_fs = os.path.join(resources_path, widget + '_ui.py')
                if os.path.exists(compiled_fs):
                    py_time = time.localtime(os.stat(compiled_fs).st_mtime)
                    if py_time >= ui_time:
                        needs_compilation = False

                if needs_compilation:
                    zfr.extract(widget + '.ui', resources_path)

        except:
            import traceback
            print(traceback.format_exc())
            raise Exception("Unable to inspect {}".format(widget + '.ui'))

        CompileUI(resources_path)

def set_plugin_icon_resources(name, resources):
    '''
    Set our global store of plugin name and icon resources for sharing between
    the InterfaceAction class which reads them and the ConfigWidget
    if needed for use on the customization dialog for this plugin.
    '''
    global plugin_icon_resources, plugin_name
    plugin_name = name
    plugin_icon_resources = resources

