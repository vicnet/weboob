# -*- coding: utf-8 -*-

# Copyright(C) 2012 Romain Bignon
#
# This file is part of a weboob module.
#
# This weboob module is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This weboob module is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this weboob module. If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals

import re
import requests
import ast

from decimal import Decimal

from weboob.browser.pages import HTMLPage, pagination, LoggedPage, FormNotFound, JsonPage
from weboob.browser.elements import method, TableElement, ItemElement
from weboob.browser.filters.standard import Env, CleanDecimal, CleanText, Date, Regexp, Eval, Field
from weboob.browser.filters.html import Attr, Link, TableCell
from weboob.browser.filters.javascript import JSVar
from weboob.capabilities.bank import Account, Investment
from weboob.capabilities.base import NotAvailable
from weboob.tools.capabilities.bank.transactions import FrenchTransaction
from weboob.tools.capabilities.bank.investments import is_isin_valid
from weboob.browser.filters.json import Dict


class LoginPage(HTMLPage):
    def login(self, login, passwd):
        tab = re.search(r'clavierAChristian = (\[[\d,\s]*\])', self.content).group(1)
        number_list = ast.literal_eval(tab)
        key_map = {}
        for i, number in enumerate(number_list):
            if number < 10:
                key_map[number] = chr(ord('A') + i)
        pass_string = ''.join(key_map[int(n)] for n in passwd)
        form = self.get_form(name='loginForm')
        form['username'] = login
        form['password'] = pass_string
        form.submit()

    def get_error(self):
        return CleanText('//div[@id="msg"]')(self.doc)


class AccountsPage(LoggedPage, HTMLPage):
    ACCOUNT_TYPES = {
        'Solde des comptes bancaires - Groupama Banque': Account.TYPE_CHECKING,
        'Solde des comptes bancaires': Account.TYPE_CHECKING,
        'Epargne bancaire constituée - Groupama Banque': Account.TYPE_SAVINGS,
        'Epargne bancaire constituée': Account.TYPE_SAVINGS,
        'Mes crédits': Account.TYPE_LOAN,
        'Assurance Vie': Account.TYPE_LIFE_INSURANCE,
        'Certificats Mutualistes': Account.TYPE_SAVINGS,
    }

    ACCOUNT_TYPES2 = {
        'plan epargne actions': Account.TYPE_PEA,
    }

    def get_list(self):
        account_type = Account.TYPE_UNKNOWN
        accounts = []

        for tr in self.doc.xpath('//div[@class="finance"]/form/table[@class="ecli"]/tr'):
            if tr.attrib.get('class', '') == 'entete':
                account_type = self.ACCOUNT_TYPES.get(tr.find('th').text.strip(), Account.TYPE_UNKNOWN)
                continue

            tds = tr.findall('td')
            a = tds[0].find('a')

            # Skip accounts that can't be accessed
            if a is None:
                continue

            balance = tds[-1].text.strip()

            account = Account()
            account.label = ' '.join([txt.strip() for txt in tds[0].itertext()])
            account.label = re.sub(r'[\s\xa0\u2022]+', ' ', account.label).strip()

            # take "N° (FOO123 456)" but "N° (FOO123) MR. BAR"
            account.id = re.search(r'N° (\w+( \d+)*)', account.label).group(1).replace(' ', '')
            account.type = account_type

            for patt, type in self.ACCOUNT_TYPES2.items():
                if patt in account.label.lower():
                    account.type = type
                    break

            if balance:
                account.balance = Decimal(FrenchTransaction.clean_amount(balance))
                account.currency = account.get_currency(balance)

            if 'onclick' in a.attrib:
                m = re.search(r"javascript:submitForm\(([\w]+),'([^']+)'\);", a.attrib['onclick'])
                if not m:
                    self.logger.warning('Unable to find link for %r', account.label)
                    account._link = None
                else:
                    account._link = m.group(2)
            else:
                account._link = a.attrib['href'].strip()

            if accounts and accounts[-1].label == account.label and account.type == Account.TYPE_PEA:
                self.logger.warning('%s seems to be a duplicate of %s, skipping', account, accounts[-1])
                continue
            accounts.append(account)
        return accounts


class Transaction(FrenchTransaction):
    PATTERNS = [
        (re.compile(r'^Facture (?P<dd>\d{2})/(?P<mm>\d{2})-(?P<text>.*) carte .*'), FrenchTransaction.TYPE_CARD),
        (re.compile(r'^(Prlv( de)?|Ech(éance|\.)) (?P<text>.*)'), FrenchTransaction.TYPE_ORDER),
        (re.compile(r'^(Vir|VIR)( de)? (?P<text>.*)'), FrenchTransaction.TYPE_TRANSFER),
        (re.compile(r'^CHEQUE.*? (N° \w+)?$'), FrenchTransaction.TYPE_CHECK),
        (re.compile(r'^Cotis(ation)? (?P<text>.*)'), FrenchTransaction.TYPE_BANK),
        (re.compile(r'(?P<text>Int .*)'), FrenchTransaction.TYPE_BANK),
        (re.compile(r'^SOUSCRIPTION|REINVESTISSEMENT'), FrenchTransaction.TYPE_DEPOSIT),
    ]


class TransactionsPage(HTMLPage):
    logged = True

    @pagination
    @method
    class get_history(Transaction.TransactionsElement):
        head_xpath = '//table[@id="releve_operation"]//tr/th'
        item_xpath = '//table[@id="releve_operation"]//tr'

        col_date = ['Date opé', 'Date', 'Date d\'opé', 'Date opération']
        col_vdate = ['Date valeur']
        col_credit = ['Crédit', 'Montant', 'Valeur']
        col_debit = ['Débit']

        def next_page(self):
            url = Attr('//a[contains(text(), "Page suivante")]', 'onclick', default=None)(self)
            if url:
                m = re.search(r'\'([^\']+).*([\d]+)', url)
                return requests.Request("POST", m.group(1),
                                        data={
                                            'numCompte': Env('accid')(self),
                                            'vue': "ReleveOperations",
                                            'tri': "DateOperation",
                                            'sens': "DESC",
                                            'page': m.group(2),
                                            'nb_element': "25"}
                                        )

        class item(Transaction.TransactionElement):
            def condition(self):
                return len(self.el.xpath('./td')) > 3

    def get_coming_link(self):
        try:
            a = self.doc.getroot().cssselect('div#sous_nav ul li a.bt_sans_off')[0]
        except IndexError:
            return None
        return re.sub(r'[\s]+', '', a.attrib['href'])

    def has_iban(self):
        return self.doc.xpath('//a[@class="rib"]')

    def go_iban(self):
        js_event = Attr("//a[@class='rib']", 'onclick')(self.doc)
        m = re.search(r'envoyer(.*);', js_event)
        iban_params = ast.literal_eval(m.group(1))
        self.browser.location("{}?paramNumCpt={}".format(iban_params[1], iban_params[0]))


class IbanPage(LoggedPage, HTMLPage):

    def get_iban(self):
        return CleanText('(//b[contains(text(), "IBAN")])[1]/../text()')(self.doc)


class AVAccountPage(LoggedPage, HTMLPage):
    """
    Get balance

    :return: decimal balance, currency
    :rtype: tuple
    """
    def get_av_balance(self):
        balance_xpath = '//p[contains(text(), "Épargne constituée")]/span'
        balance = CleanDecimal(balance_xpath)(self.doc)
        currency = Account.get_currency(CleanText(balance_xpath)(self.doc))
        return balance, currency

    @method
    class get_av_investments(TableElement):
        item_xpath = '//table[@id="repartition_epargne3"]/tr[position() > 1]'
        head_xpath = '//table[@id="repartition_epargne3"]/tr/th[position() > 1]'

        col_quantity = 'Nombre d’unités de compte'
        col_unitvalue = "Valeur de l’unité de compte"
        col_valuation = 'Épargne constituée en euros'
        col_portfolio_share = 'Répartition %'

        class item(ItemElement):
            klass = Investment

            def condition(self):
                return (CleanText('./th')(self) != 'Total épargne constituée') and ('Détail' not in Field('label')(self))

            obj_label = CleanText('./th')
            obj_quantity = CleanDecimal(TableCell('quantity'), default=NotAvailable)
            obj_unitvalue = CleanDecimal(TableCell('unitvalue'), default=NotAvailable)
            obj_valuation = CleanDecimal(TableCell('valuation'), default=NotAvailable)
            obj_portfolio_share = Eval(lambda x: x / 100, CleanDecimal(TableCell('portfolio_share')))

            def obj_code(self):
                code = Regexp(Link('./th/a', default=''), r'isin=(\w+)|/(\w+)\.pdf', default=NotAvailable)(self)
                return code if is_isin_valid(code) else NotAvailable

            def obj_code_type(self):
                return Investment.CODE_TYPE_ISIN if is_isin_valid(Field('code')(self)) else NotAvailable


class AvJPage(LoggedPage, JsonPage):
    def get_av_balance(self):
        balance = CleanDecimal(Dict('montant'))(self.doc)
        currency = "EUR"
        return balance, currency


class AVHistoryPage(LoggedPage, HTMLPage):
    @method
    class get_av_history(TableElement):
        item_xpath = '//table[@id="enteteTableSupports"]/tbody/tr'
        head_xpath = '//table[@id="enteteTableSupports"]/thead/tr/th'

        col_date = 'Date'
        col_label = 'Type de mouvement'
        col_debit = 'Montant Désinvesti'
        col_credit = ['Montant investi', 'Montant Net Perçu']
        # There is several types of life insurances, so multiple columns
        col_credit2 = ['Montant Brut Versé']

        class item(ItemElement):
            klass = Transaction

            def condition(self):
                return CleanText(TableCell('date'))(self) != 'en cours'

            obj_label = CleanText(TableCell('label'))
            obj_type = Transaction.TYPE_BANK
            obj_date = Date(CleanText(TableCell('date')), dayfirst=True)
            obj__arbitration = False

            def obj_amount(self):
                credit = CleanDecimal(TableCell('credit'), default=Decimal(0))(self)
                # Different types of life insurances, use different columns.
                if TableCell('debit', default=None)(self):
                    debit = CleanDecimal(TableCell('debit'), default=Decimal(0))(self)
                    # In case of financial arbitration, both columns are equal
                    if credit and debit:
                        assert credit == debit
                        self.obj._arbitration = True
                        return credit
                    else:
                        return credit - abs(debit)
                else:
                    credit2 = CleanDecimal(TableCell('credit2'), default=Decimal(0))(self)
                    assert not (credit and credit2)
                    return credit + credit2


class FormPage(LoggedPage, HTMLPage):
    def get_av_balance(self):
        balance_xpath = '//p[contains(text(), "montant de votre épargne")]'
        balance = CleanDecimal(Regexp(CleanText(balance_xpath), r'est de ([\s\d,]+)', default=NotAvailable),
                               replace_dots=True, default=NotAvailable)(self.doc)
        currency = Account.get_currency(CleanText(balance_xpath)(self.doc))
        return balance, currency

    def av_account_form(self):
        try:
            form = self.get_form(id="formGoToRivage")
            form['gfr_numeroContrat'] = JSVar(var='numContrat').filter(CleanText('//script[contains(text(), "var numContrat")]')(self.doc))
            form['gfr_data'] = JSVar(var='pCryptage').filter(CleanText('//script[contains(text(), "var pCryptage")]')(self.doc))
            form['gfr_adrSite'] = 'https://espaceclient.%s.fr' % self.browser.website
            form.url = 'https://secure-rivage.%s.fr/contratVie.rivage.syntheseContratEparUc.gsi' % self.browser.website
            form.submit()
            return True
        except FormNotFound:
            return False
