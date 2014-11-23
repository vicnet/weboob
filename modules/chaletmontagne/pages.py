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
from weboob.browser.filters.standard import CleanText, Regexp, CleanDecimal, MultiFilter, debug, Format, Env, _NO_DEFAULT, BrowserURL
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
            obj_title = Format('%s - %s'
                , CleanText('.//div[@class="une-location-texte"]/p/span')
                , CleanText('.//div[@class="une-location-texte"]/p/text()')
                )
            obj_area = CleanDecimal(Regexp(CleanText('.//img[contains(@src,"picto-surface")]/..'),
                                           '(\d*)', '\\1'), default=NotAvailable)
            obj_cost = CleanDecimal(Regexp(CleanText('.//div[@class="location-tranche-prix"]'),
                                           '(\d*)', '\\1'), default=NotAvailable)
            obj_currency = u'€'
            obj_location = CleanText('.//div[@class="une-location-texte"]/p/span[2]')
            obj_text = CleanText('.//div[@class="une-location-interieur-hover"]//div[@class="une-location-texte"]')
            def obj_details(self):
                details = {}
                details['capacity'] = CleanText('.//img[contains(@src,"picto-nb-personnes")]/..')(self)
                details['rooms'] = CleanText('.//img[contains(@src,"picto-chambre")]/..')(self)
                return details
            obj_url = Format('https://www.chalet-montagne.com%s',Attr('./a','href'))

class CleanTextByText(CleanText):
    def __init__(self, selector=None, default=_NO_DEFAULT):
        super(CleanTextByText, self).__init__(
              selector='.//strong[contains(text(),"%s")]/../../..//td[last()]'%selector
            , default=default
            )

class HousingPage(HTMLPage):
    @method
    class get_housing(ItemElement):
        klass = Housing

        obj_id = Regexp(CleanText('.//span[contains(text(),"Location :")]'), '(\d+)', '\\1')
        obj_title = Format('%s - %s'
            , CleanTextByText('Type de location')
            , CleanText('.//span[contains(text(),"Location :")]/text()[2]')
            )
        obj_text = CleanTextByText('Station principale')
        obj_date = NotAvailable
        obj_cost = NotAvailable
        obj_currency = NotAvailable
        obj_area = CleanDecimal(Regexp(CleanTextByText('Surface'),'(\d+)','\\1'))
        obj_location = CleanTextByText('Code postal')
        obj_station = NotAvailable
        obj_url = obj_url = BrowserURL('housing', id=Env('id'))
        obj_phone = Regexp(CleanText('.//p[contains(text(),"Tel :")]/text()[1]'),'Tel : (.*)', '\\1')
        def obj_details(self):
            details = {}
            details['capacity'] = CleanTextByText('Capacit')(self)
            details['rooms'] = CleanTextByText('Chambre(s)')(self)
            details['remarques'] = CleanTextByText('Remarques')(self)
            return details
