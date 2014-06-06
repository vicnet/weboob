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

from weboob.tools.browser2.page import HTMLPage, method,pagination, ListElement, ItemElement
from weboob.tools.browser2.filters import MultiFilter, Link, CleanText, Regexp
from weboob.capabilities.housing import Housing


__all__ = ['LoginPage', 'HostlistPage', 'ProfilePage']


class LoginPage(HTMLPage):
    def login(self, login, password):
        form = self.get_form(xpath='//form[@id="user-login"]')
        form['name'] = login
        form['pass'] = password
        form.submit()

class HostlistPage(HTMLPage):
    @pagination
    @method
    class search_housings(ListElement):
        item_xpath = '//tr[contains(@class,"hostlist-row")]'
        
        next_page = Link('//a[@title="Go to next page"]')
        
        class item(ItemElement):
            klass = Housing
            
            obj_id = Regexp(Link('.//a'),r'/profile/(.+)')
            obj_title = CleanText('.//a')
            obj_text = CleanText('.//p[@class="site-description"]')
            obj_cost = 0
            obj_currency = u'€'
            obj_area = 0

class ProfilePage(HTMLPage):
    @method
    class get_housing(ItemElement):
        klass = Housing

        obj_title = CleanText('.//h1')
        obj_text = CleanText('.//div[contains(@class,"host-site-desc")]')
        obj_phone = CleanText('.//div[contains(@class,"host-tel1")]')
        obj_cost = 0
        obj_currency = u'€'
        obj_area = 0
        
        def getField(self, tag):
            base = './/div[contains(@class,"%s")]' % tag
            return [(CleanText('%s/div[1]' % base)(self)
                   , CleanText('%s/div[2]' % base)(self))]

        def obj_details(self):
            #base = '//div[contains(@class,"group-host-data")]'
            res = dict()
            res.update(self.getField('host-sitetype'))
            res.update(self.getField('host-organic-status'))
            res.update(self.getField('host-accommodation'))
            res.update(self.getField('host-food'))
            res.update(self.getField('host-smoking'))
            res.update(self.getField('host-months'))
            res.update(self.getField('host-nearest-town'))
            return res
