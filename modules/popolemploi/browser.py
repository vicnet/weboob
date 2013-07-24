# -*- coding: utf-8 -*-

# Copyright(C) 2013      Bezleputh
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

from weboob.tools.browser.decorators import id2url
from weboob.tools.browser import BaseBrowser

from .pages import SearchPage, AdvertPage
from .job import PopolemploiJobAdvert


__all__ = ['PopolemploiBrowser']


class PopolemploiBrowser(BaseBrowser):
    PROTOCOL = 'http'
    DOMAIN = 'http://www.pole-emploi.fr/accueil/'
    ENCODING = None

    PAGES = {
        'http://candidat.pole-emploi.fr/candidat/rechercheoffres/resultats(.*?)': SearchPage,
        'http://candidat.pole-emploi.fr/candidat/rechercheoffres/detail/(?P<id>.+)': AdvertPage,
    }

    def search_job(self, pattern=None):
        self.location('http://offre.pole-emploi.fr/resultat?offresPartenaires=true&libMetier=%s'
                      % pattern.replace(' ', '+'))
        assert self.is_on_page(SearchPage)
        return self.page.iter_job_adverts()

    @id2url(PopolemploiJobAdvert.id2url)
    def get_job_advert(self, url, advert):
        self.location(url)
        assert self.is_on_page(AdvertPage)
        return self.page.get_job_advert(url, advert)
