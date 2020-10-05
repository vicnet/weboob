# -*- coding: utf-8 -*-

# Copyright(C) 2014 Vicnet
#
# This file is part of a weboob module.
#
# This weboob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This weboob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this weboob module. If not, see <http://www.gnu.org/licenses/>.

from weboob.capabilities.pricecomparison import CapPriceComparison, Price
from weboob.tools.backend import Module
from .product import LaCentraleProduct

from .browser import LaCentraleBrowser


__all__ = ['LaCentraleModule']


class LaCentraleModule(Module, CapPriceComparison):
    NAME = 'lacentrale'
    MAINTAINER = u'Vicnet'
    EMAIL = 'vo.publique@gmail.com'
    VERSION = '2.1'
    DESCRIPTION = 'Vehicule prices at LaCentrale.fr'
    LICENSE = 'AGPLv3+'
    BROWSER = LaCentraleBrowser

    def search_products(self, patternString=None):
        criteria = {}
        patterns = []
        if patternString:
            patterns = patternString.split(',')
        for pattern in patterns:
            pattern = pattern.lower()
            if u'€' in pattern:
                criteria['priceMax'] = pattern[:pattern.find(u'€')].strip()
            elif u'km' in pattern:
                criteria['km_maxi'] = pattern[:pattern.find(u'km')].strip()
            elif u'p' in pattern[-1]:  # last char = p
                criteria['nbdoors'] = pattern[:pattern.find(u'p')].strip()
            elif u'cit' in pattern:
                criteria['Citadine'] = 'citadine&SS_CATEGORIE=40'
            elif u'dep' in pattern:
                criteria['dptCp'] = pattern.replace('dep', '')
            elif u'pro' in pattern:
                criteria['witchSearch'] = 1
            elif u'part' in pattern:
                criteria['witchSearch'] = 0
            elif u'diesel' in pattern:
                criteria['energie'] = 2
            elif u'essence' in pattern:
                criteria['energie'] = 1
            elif u'electrique' in pattern:
                criteria['energie'] = 4
            elif u'hybride' in pattern:
                criteria['energie'] = '8,9'
            else:
                criteria['makesModelsCommercialNames'] = pattern
        print(f'criteria {criteria}')
        if criteria:
            product = LaCentraleProduct()
            product._criteria = criteria
            yield product

    def iter_prices(self, products):
        product = [product for product in products if product.backend == self.name]
        if product:
            return self.browser.iter_prices(product[0])

    def get_price(self, id, price=None):
        return self.browser.get_price(id, None)

    def fill_price(self, price, fields):
        if fields:
            price = self.get_price(price.id, price)
        return price

    OBJECTS = {Price: fill_price, }
