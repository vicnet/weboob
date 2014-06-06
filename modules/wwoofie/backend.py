# -*- coding: utf-8 -*-

# Copyright(C) 2014      Vicnet
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

from weboob.tools.backend import BaseBackend, BackendConfig
from weboob.tools.value import ValueBackendPassword#,Value, ValueBool
from weboob.capabilities.housing import ICapHousing, City, Housing

from .browser import WwoofieBrowser

__all__ = ['WwoofieBackend']


class WwoofieBackend(BaseBackend, ICapHousing):
    NAME = 'wwoofie'
    DESCRIPTION = u'wwoof.ie website'
    MAINTAINER = u'Vicnet'
    EMAIL = 'vo.publique@gmail.com'
    LICENSE = 'AGPLv3+'
    VERSION = '0.j'
    CONFIG = BackendConfig(ValueBackendPassword('login',
                                                label='Username',
                                                masked=False),
                           ValueBackendPassword('password',
                                                label='Password')
                           )
    BROWSER = WwoofieBrowser

    def create_default_browser(self):
        return self.create_browser(self.config['login'].get(),
                                   self.config['password'].get())

    def search_city(self, pattern):
        c = City('munster')
        c.name = u'Munster'
        yield c

    def search_housings(self, query):
        cities = [c.id for c in query.cities if c.backend == self.name]
        if len(cities) == 0:
            return list([])

        return self.browser.search_housings()

    def get_housing(self, housing):
        if isinstance(housing, Housing):
            id = housing.id
        else:
            id = housing

        return self.browser.get_housing(id)
