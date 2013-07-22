# -*- coding: utf-8 -*-

# Copyright(C) 2013      Laurent Bachelier
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


from weboob.tools.browser import BaseBrowser, BrowserIncorrectPassword
from weboob.tools.ordereddict import OrderedDict

from .pages import LoginPage, AccountsPage, HistoryPage


__all__ = ['SGProfessionalBrowser', 'SGEnterpriseBrowser']


class SGPEBrowser(BaseBrowser):
    PROTOCOL = 'https'
    ENCODING = 'ISO-8859-1'

    def __init__(self, *args, **kwargs):
        self.PAGES = OrderedDict((
            ('%s://%s/Pgn/.+PageID=SoldeV3&.+' % (self.PROTOCOL, self.DOMAIN), AccountsPage),
            ('%s://%s/Pgn/.+PageID=ReleveCompteV3&.+' % (self.PROTOCOL, self.DOMAIN), HistoryPage),
            ('%s://%s/' % (self.PROTOCOL, self.DOMAIN), LoginPage),
        ))
        BaseBrowser.__init__(self, *args, **kwargs)

    def is_logged(self):
        if not self.page or self.is_on_page(LoginPage):
            return False

        error = self.page.get_error()
        if error is None:
            return True

        return False

    def login(self):
        assert isinstance(self.username, basestring)
        assert isinstance(self.password, basestring)
        assert self.password.isdigit()

        if not self.is_on_page(LoginPage):
            self.location('https://' + self.DOMAIN + '/', no_login=True)

            self.page.login(self.username, self.password)

        # force page change
        if not self.is_on_page(AccountsPage):
            self.accounts()
        if self.is_on_page(LoginPage):
            raise BrowserIncorrectPassword()

    def accounts(self):
        self.location('/Pgn/NavigationServlet?PageID=SoldeV3&MenuID=%s&Classeur=1&NumeroPage=1' % self.MENUID)

    def history(self, _id, page=1):
        if page > 1:
            pgadd = '&page_numero_page_courante=%s' % page
        else:
            pgadd = ''
        self.location('/Pgn/NavigationServlet?PageID=ReleveCompteV3&MenuID=%s&Classeur=1&Rib=%s&NumeroPage=1%s' % (self.MENUID, _id, pgadd))

    def get_accounts_list(self):
        if not self.is_on_page(AccountsPage):
            self.accounts()
        assert self.is_on_page(AccountsPage)
        return self.page.get_list()

    def get_account(self, _id):
        for a in self.get_accounts_list():
            if a.id == _id:
                yield a

    def iter_history(self, account):
        page = 1
        while page:
            self.history(account.id, page)
            assert self.is_on_page(HistoryPage)
            for transaction in self.page.iter_transactions(account):
                yield transaction
            if self.page.has_next():
                page += 1
            else:
                page = False


class SGProfessionalBrowser(SGPEBrowser):
    DOMAIN = 'professionnels.secure.societegenerale.fr'
    LOGIN_FORM = 'auth_reco'
    MENUID = 'SBORELCPT'


class SGEnterpriseBrowser(SGPEBrowser):
    DOMAIN = 'entreprises.secure.societegenerale.fr'
    LOGIN_FORM = 'auth'
    MENUID = 'BANRELCPT'
