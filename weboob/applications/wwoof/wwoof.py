# -*- coding: utf-8 -*-

# Copyright(C) 2012 Vicnet
#
# This file is part of weboob.
#
# weboob is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# weboob is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with weboob. If not, see <http://www.gnu.org/licenses/>.


import sys

from weboob.capabilities.housing import ICapHousing, Query
from weboob.tools.application.repl import ReplApplication, defaultcount
from weboob.tools.application.formatters.iformatter import IFormatter, PrettyFormatter


__all__ = ['Wwoof']


class HousingFormatter(IFormatter):
    MANDATORY_FIELDS = ('id', 'title', 'cost', 'currency', 'area', 'date', 'text')

    def format_obj(self, obj, alias):
        result = u'%s%s%s\n' % (self.BOLD, obj.title, self.NC)
        result += 'ID: %s\n' % obj.fullid
        result += 'Cost: %s%s\n' % (obj.cost, obj.currency)
        result += u'Area: %sm²\n' % (obj.area)
        if obj.date:
            result += 'Date: %s\n' % obj.date.strftime('%Y-%m-%d')
        result += 'Phone: %s\n' % obj.phone
        if hasattr(obj, 'location') and obj.location:
            result += 'Location: %s\n' % obj.location
        if hasattr(obj, 'station') and obj.station:
            result += 'Station: %s\n' % obj.station

        if hasattr(obj, 'photos') and obj.photos:
            result += '\n%sPhotos%s\n' % (self.BOLD, self.NC)
            for photo in obj.photos:
                result += ' * %s\n' % photo.url

        result += '\n%sDescription%s\n' % (self.BOLD, self.NC)
        result += obj.text

        if hasattr(obj, 'details') and obj.details:
            result += '\n\n%sDetails%s\n' % (self.BOLD, self.NC)
            for key, value in obj.details.iteritems():
                result += ' %s: %s\n' % (key, value)
        return result

class Wwoof(ReplApplication):
    APPNAME = 'flatboob'
    VERSION = '0.j'
    COPYRIGHT = 'Copyright(C) 2012 Romain Bignon'
    DESCRIPTION = "Console application to search for housing."
    SHORT_DESCRIPTION = "search for housing"
    CAPS = ICapHousing
    EXTRA_FORMATTERS = {'housing_list': HousingFormatter, }
    COMMANDS_FORMATTERS = {'search': 'housing_list', }

    def main(self, argv):
        self.load_config()
        return ReplApplication.main(self, argv)

    @defaultcount(10)
    def do_search(self, line):
        """
        search

        Search for housing. Parameters are interactively asked.
        """
        query = Query()

        self.change_path([u'housings'])
        ids = []
        for backend, housing in self.do('search_housings', query):
            ids.append(housing.fullid)

        self.start_format()
        for id in ids:
            housing = self.get_object(id, 'get_housing')
            if not housing:
                print >>sys.stderr, 'Housing not found: %s' % housing.fullid
                return 3
            self.format(housing)

    def complete_info(self, text, line, *ignored):
        args = line.split(' ')
        if len(args) == 2:
            return self._complete_object()

