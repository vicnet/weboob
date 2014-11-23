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

from weboob.browser import PagesBrowser, URL
from weboob.capabilities.housing import Query
from .pages import IndexPage, HousingListPage, HousingPage


class ChaletMontagneBrowser(PagesBrowser):
    BASEURL = 'https://www.chalet-montagne.com'
    index = URL('/$', IndexPage)
    search = URL('/ajax/(?P<station>.*)/(?P<begin>.*)/(?P<end>.*)/null/rechercher-une-location-ajax', HousingListPage)
    housing = URL('http://www.chalet-montagne.com/mobile/details.php\?id=(?P<id>.*)', HousingPage)

    def get_cities(self, pattern):
        for city in self.index.stay_or_go().get_cities():
            if not pattern.lower() in city.name.lower():
                continue
            yield city

    def search_housings(self, query):
        data = {
              'data[0][]':'prix'
            , 'data[0][]':'0 - 22222'
            , 'data[1][]':'typeLogement'
            , 'data[1][]':''
            , 'directionTri':'ASC'
            , 'infiniteScroll':'oui'
            #, 'nbElemCourant':'10912'
            , 'valeurTri':''
            }
        while True:
            lastid = None
            for housing in self.search.go(data=data, station=query.cities[0].id, begin='14-02-2015', end='21-02-2015').get_housing_list():
                lastid = housing.id
                yield housing
            if lastid==None:
                return
            data['nbElemCourant'] = lastid

    def get_housing(self, id, housing=None):
        return self.housing.go(id=id).get_housing(obj=housing)
