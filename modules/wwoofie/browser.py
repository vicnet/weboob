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

from weboob.tools.browser2 import LoginBrowser, URL, need_login#, Profile, Firefox
from weboob.tools.browser import BrowserIncorrectPassword
from .pages import LoginPage, HostlistPage


__all__ = ['WwoofieBrowser']


class WwoofieBrowser(LoginBrowser):
    BASEURL = 'http://www.wwoof.ie'

    hostlist = URL('/hostlist/full/munster/all', HostlistPage)
    login = URL('/user', LoginPage)

    def do_login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)

        self.login.stay_or_go().login(self.username, self.password)

        # test if success
        #self.homepage.go()
        #if self.login.is_here():
        #raise BrowserIncorrectPassword()

    @need_login
    def search_housings(self):
        return self.hostlist.stay_or_go().search_housings()
