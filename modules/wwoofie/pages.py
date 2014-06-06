# -*- coding: utf-8 -*-

# Copyright(C) 2014  Vicnet
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

from weboob.tools.browser2.page import HTMLPage, method, ListElement, ItemElement
from weboob.tools.browser2.filters import Link, CleanText, Regexp
from weboob.capabilities.housing import Housing


__all__ = ['LoginPage', 'HostlistPage']


class LoginPage(HTMLPage):
    def login(self, login, password):
        form = self.get_form(xpath='//form[@id="user-login"]')
        form['name'] = login
        form['pass'] = password
        form.submit()

class HostlistPage(HTMLPage):
    @method
    class search_housings(ListElement):
        item_xpath = '//tr[contains(@class,"hostlist-row")]'
        
        class item(ItemElement):
            klass = Housing
            
            obj_id = Regexp(Link('.//a'),r'/profile/(.+)')
            obj_title = CleanText('.//a')
            obj_text = CleanText('.//p[@class="site-description"]')
