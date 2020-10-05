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

from weboob.browser import PagesBrowser, URL

from .pages import ListingAutoPage, AdvertPage

__all__ = ['LaCentraleBrowser']


class LaCentraleBrowser(PagesBrowser):
    BASEURL = 'https://www.lacentrale.fr'

    list_page = URL('/listing\?(?P<_request>.*)', ListingAutoPage)
    ref_page  = URL('/listing\?reference=(?P<_id>.*)', ListingAutoPage)
    auto_page = URL('/auto-occasion-annonce-(?P<_id>.*).html', AdvertPage)
    util_page = URL('/utilitaire-occasion-annonce-(?P<_id>.*).html', AdvertPage)

    def iter_prices(self, product):
        _request = '&'.join(['%s=%s' % (key, item) for key, item in product._criteria.items()])
        return self.list_page.go(_request=_request).iter_prices()

    def get_price(self, _id, obj):
        #prices = self.ref_page.go(_id=_id).iter_prices()
        #price = next(prices, None)
        #if price is None:
            #return None
        #if 'utilitaire' in price.url:
            #return self.util_page.go(_id=_id).get_price(obj=obj)
        return self.auto_page.go(_id=_id).get_price(obj=obj)
