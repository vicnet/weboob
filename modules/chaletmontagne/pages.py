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
from weboob.browser.pages import HTMLPage, pagination
from weboob.browser.elements import ItemElement, ListElement, method
from weboob.browser.filters.standard import CleanText, Regexp, CleanDecimal
from weboob.browser.filters.html import Attr, Link
from weboob.capabilities.housing import City, Housing, HousingPhoto
from weboob.capabilities.base import NotAvailable


class IndexPage(HTMLPage):
    @method
    class get_cities(ListElement):
        item_xpath = '//optgroup[@label="Stations"]/option'

        class item(ItemElement):
            klass = City

            obj_id = Attr('.', 'value')
            obj_name = CleanText('.')

class HousingListPage(HTMLPage):
    @method
    class get_housing_list(ListElement):
        item_xpath = '//div[@class="une-location"]'

        class item(ItemElement):
            klass = Housing

            obj_id = Attr('.', 'id')
            obj_title = CleanText('.//div[@class="une-location-texte"]/p')
            obj_area = CleanDecimal(Regexp(CleanText('.//img[contains(@src,"picto-surface")]/..'),
                                           '(\d*)', '\\1'), default=NotAvailable)
            obj_cost = CleanDecimal(Regexp(CleanText('.//div[@class="location-tranche-prix"]'),
                                           '(\d*)', '\\1'), default=NotAvailable)
            obj_currency = u'€'
            obj_location = CleanText('.//div[@class="une-location-texte"]/p/span[2]')
            obj_text = CleanText('.//div[@class="une-location-interieur-hover"]//div[@class="une-location-texte"]')
            def obj_details(self):
                details = {}
                details['nb-personnes'] = CleanText('.//img[contains(@src,"picto-nb-personnes")]/..')(self)
                details['chambre'] = CleanText('.//img[contains(@src,"picto-chambre")]/..')(self)
                return details
