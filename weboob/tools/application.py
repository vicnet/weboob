# -*- coding: utf-8 -*-

"""
Copyright(C) 2010  Romain Bignon

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.

"""

import sys, tty, termios, os
import re
from functools import partial
from inspect import getargspec

from weboob import Weboob

class BaseApplication(object):
    # Application name
    APPNAME = ''
    # Default configuration
    CONFIG = {}
    # Configuration directory
    CONFDIR = os.path.join(os.path.expanduser('~'), '.weboob')

    def __init__(self):
        self.weboob = Weboob(self.APPNAME)
        self.config = None

    def load_config(self, path=None, klass=None):
        """
        Load a configuration file and get his object.

        @param path [str]  an optional specific path.
        @param klass [IConfig]  what klass to instance.
        @return  a IConfig object
        """
        if klass is None:
            # load Config only here because some applications don't want
            # to depend on yaml and do not use this function
            from weboob.tools.config.yamlconfig import YamlConfig
            klass = YamlConfig

        if path is None:
            path = os.path.join(self.CONFDIR, self.APPNAME)
        elif not path.startswith('/'):
            path = os.path.join(self.CONFDIR, path)

        self.config = klass(path)
        self.config.load(self.CONFIG)

    def main(self, argv):
        """ Main function """
        raise NotImplementedError()

    @classmethod
    def run(klass):
        app = klass()
        sys.exit(app.main(sys.argv))

class ConsoleApplication(BaseApplication):
    def ask(self, question, default=None, masked=False, regexp=None):
        """
        Ask a question to user.

        @param question  text displayed (str)
        @param default  optional default value (str)
        @param masked  if True, do not show typed text (bool)
        @param regexp  text must match this regexp (str)
        @return  entered text by user (str)
        """

        correct = False

        if not default is None:
            question = '%s [%s]' % (question, default)

        while not correct:
            sys.stdout.write('%s: ' % (question))

            if masked:
                attr = termios.tcgetattr(sys.stdin)
                tty.setcbreak(sys.stdin)

            line = sys.stdin.readline().split('\n')[0]

            if not line and not default is None:
                line = default

            if masked:
                termios.tcsetattr(sys.stdin, termios.TCSAFLUSH, attr)
                sys.stdout.write('\n')

            correct = not regexp or re.match(regexp, str(line))

        return line

    def process_command(self, command='help', *args):
        def f(x):
            return x.startswith('command_' + command)

        matching_commands = filter(f, dir(self))

        if len(matching_commands) == 0:
            sys.stderr.write("No such command: %s.\n" % command)
        elif len(matching_commands) == 1:
            try:
                getattr(self, matching_commands[0])(*args)
            except TypeError, e:
                try:
                    sys.stderr.write("Command '%s' takes %s arguments.\n" % \
                            (command, int(str(e).split(' ')[3]) - 1))
                except:
                    sys.stderr.write('%s\n' % e)
        else:
            sys.stderr.write("Ambiguious command %s: %s.\n" %
                             (command,
                              ', '.join([s.replace('command_', '', 1)
                                                for s in matching_commands])))


    _command_help = []
    def register_command(f, doc_string, register_to=_command_help):
        def getArguments(func, skip=0):
            """
            Get arguments of a function as a string.
            skip is the number of skipped arguments.
            """
            skip += 1
            args, varargs, varkw, defaults = getargspec(func)
            cut = len(args)
            if defaults:
                cut -= len(defaults)
            args = ["<%s>" % a for a in args[skip:cut]] + \
                   ["[%s]" % a for a in args[cut:]]
            if varargs:
                args.append("[*%s]" % varargs)
            if varkw:
                args.append("[**%s]" % varkw)
            return " ".join(args)

        command = '%s %s' % (f.func_name.replace('command_', ''),
                             getArguments(f))
        register_to.append('%-30s %s' % (command, doc_string))
        return f

    def command(doc_string, f=register_command):
        return partial(f, doc_string=doc_string)

    @command("display this notice")
    def command_help(self):
        sys.stdout.write("Available commands:\n")
        for f in self._command_help:
            sys.stdout.write('   %s\n' % f)

    register_command = staticmethod(register_command)
    command = staticmethod(command)
