# -*- coding: utf-8 -*-

# +---------------------------------------------------------------------------+
# | pylstar : Implementation of the LSTAR Grammatical Inference Algorithm     |
# +---------------------------------------------------------------------------+
# | Copyright (C) 2015 Georges Bossert                                        |
# | This program is free software: you can redistribute it and/or modify      |
# | it under the terms of the GNU General Public License as published by      |
# | the Free Software Foundation, either version 3 of the License, or         |
# | (at your option) any later version.                                       |
# |                                                                           |
# | This program is distributed in the hope that it will be useful,           |
# | but WITHOUT ANY WARRANTY; without even the implied warranty of            |
# | MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the              |
# | GNU General Public License for more details.                              |
# |                                                                           |
# | You should have received a copy of the GNU General Public License         |
# | along with this program. If not, see <http://www.gnu.org/licenses/>.      |
# +---------------------------------------------------------------------------+
# | @url      : https://github.com/gbossert/pylstar                           |
# | @contact  : gbossert@miskin.fr                                            |
# +---------------------------------------------------------------------------+

#+---------------------------------------------------------------------------+
#| Standard library imports                                                  |
#+---------------------------------------------------------------------------+
import logging
logging.basicConfig(level=logging.DEBUG)

#+---------------------------------------------------------------------------+
#| Related third party imports                                               |
#+---------------------------------------------------------------------------+
from functools import wraps

#+---------------------------------------------------------------------------+
#| Local application imports                                                 |
#+---------------------------------------------------------------------------+

# Definition of the ColorStreamHandler class only if dependency colorama is
# available on the current system.
try:
    from colorama import Fore, Back, Style

    class ColourStreamHandler(logging.StreamHandler):
        """ A colorized output SteamHandler """

        # Some basic colour scheme defaults
        colours = {
            'DEBUG': Fore.CYAN,
            'INFO': Fore.GREEN,
            'WARN': Fore.YELLOW,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRIT': Back.RED + Fore.WHITE,
            'CRITICAL': Back.RED + Fore.WHITE
        }

        @property
        def is_tty(self):
            """ Check if we are using a "real" TTY. If we are not using a TTY it means that
            the colour output should be disabled.

            :return: Using a TTY status
            :rtype: bool
            """
            try:
                return getattr(self.stream, 'isatty', None)()
            except:
                return False

        def emit(self, record):
            try:
                message = self.format(record)

                if not self.is_tty:
                    self.stream.write(message)
                else:
                    self.stream.write(self.colours[record.levelname] + message + Style.RESET_ALL)
                self.stream.write(getattr(self, 'terminator', '\n'))
                self.flush()
            except (KeyboardInterrupt, SystemExit):
                raise
            except:
                self.handleError(record)

    has_colour = True
except Exception, e:
    has_colour = False


def PylstarLogger(klass):
    """This class decorator adds (if necessary) an instance
    of the logger (self.__logger) to the attached class
    and removes from the getState the logger.

    """

    # Verify if a logger already exists
    found = False
    for k, v in klass.__dict__.iteritems():
        if isinstance(v, logging.Logger):
            found = True
            break
    if not found:
        klass._logger = logging.getLogger(klass.__name__)
        handler = ColourStreamHandler() if has_colour else logging.StreamHandler()
        handler.setLevel(logging.DEBUG)
        fmt = '%(relativeCreated)d: [%(levelname)s] %(module)s:%(funcName)s: %(message)s'
        handler.setFormatter(logging.Formatter(fmt))
        klass._logger.addHandler(handler)
        klass._logger.propagate = False

    # Exclude logger from __getstate__
    def getState(self, **kwargs):
        r = dict()
        for k, v in self.__dict__.items():
            if not isinstance(v, logging.Logger):
                r[k] = v
        return r

    def setState(self, dict):
        self.__dict__ = dict
        self.__logger = logging.getLogger(klass.__name__)

    klass.__getstate__ = getState
    klass.__setState__ = setState

    return klass


def typeCheck(*types):
    """Decorator which reduces the amount of code to type-check attributes.

    Its allows to replace the following code:
    ::
        @id.setter
        def id(self, id):
            if not isinstance(id, uuid.UUID):
               raise TypeError("Invalid types for argument id, must be an UUID")
            self.__id = id

    with:
    ::
        @id.setter
        @typeCheck(uuid.UUID)
        def id(self, id):
           self.__id = id

    .. note:: set type = "SELF" to check the type of the self parameter
    .. warning:: if argument is None, the type checking is not executed on it.

    """
    def _typeCheck_(func):
        def wrapped_f(*args, **kwargs):
            arguments = args[1:]
            if len(arguments) == len(types):
                # Replace "SELF" with args[0] type
                final_types = []
                for type in types:
                    if type == "SELF":
                        final_types.append(args[0].__class__)
                    else:
                        final_types.append(type)

                for i, argument in enumerate(arguments):
                    if argument is not None and not isinstance(argument, final_types[i]):
                        raise TypeError("Invalid type for arguments, expecting: {0} and received {1}".format(', '.join([t.__name__ for t in final_types]), argument.__class__.__name__))
            return func(*args, **kwargs)
        return wraps(func)(wrapped_f)
    return _typeCheck_