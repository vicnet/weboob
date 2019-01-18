# -*- coding: utf-8 -*-

# Copyright(C) 2012-2019  Budget Insight
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

from decimal import Decimal
import re
import datetime

from weboob.browser.pages import JsonPage, LoggedPage
from weboob.browser.elements import ItemElement, DictElement, method
from weboob.browser.filters.standard import CleanText, Date, Regexp, CleanDecimal, Env, Field, RegexpError
from weboob.browser.filters.json import Dict
from weboob.capabilities.bank import Account, Investment
from weboob.capabilities.base import NotAvailable
from weboob.tools.capabilities.bank.transactions import FrenchTransaction
from weboob.exceptions import AuthMethodNotImplemented, ParseError
from weboob.tools.capabilities.bank.investments import is_isin_valid


def MyDecimal(*args, **kwargs):
    kwargs.update(replace_dots=True, default=NotAvailable)
    return CleanDecimal(*args, **kwargs)


class LoginPage(JsonPage):
    def on_load(self):
        if Dict('statusText', default="")(self.doc) == "totpNeeded":
            raise AuthMethodNotImplemented("Time-based One-time Password is not supported")

    def get_session_id(self):
        return Dict('sessionId')(self.doc)

    def get_information(self, information):
        return Dict(information, default=None)(self.doc)


def list_to_dict(l):
    return {d['name']: d.get('value') for d in l}


class AccountsPage(LoggedPage, JsonPage):
    @method
    class get_account(ItemElement):
        klass = Account

        def obj_balance(self):
            return CleanDecimal().filter(sum(
                [round(y['value'], 2) for x in Dict('portfolio/value')(self) for y in x['value'] if y['name'] == 'value']
                ))

        def obj_id(self):
            return str(self.page.browser.intAccount)

        def obj_label(self):
            return '%s DEGIRO' % self.page.browser.name.title()

        def obj_type(self):
            return Account.TYPE_MARKET

        def obj_currency(self):
            for currency in Dict('cashFunds/value')(self):
                if Dict('value/2/value' % currency)(currency) != 0:
                    return Dict('value/1/value')(currency)

    @method
    class iter_investment(DictElement):
        item_xpath = 'portfolio/value'

        class item(ItemElement):
            klass = Investment

            def condition(self):
                return Decimal(str(list_to_dict(self.el['value'])['size']))

            obj_unitvalue = Env('unitvalue', default=NotAvailable)
            obj_original_currency = Env('original_currency', default=NotAvailable)
            obj_original_unitvalue = Env('original_unitvalue', default=NotAvailable)

            def obj__product_id(self):
                return str(list_to_dict(self.el['value'])['id'])

            def obj_quantity(self):
                return Decimal(str(list_to_dict(self.el['value'])['size']))

            def obj_valuation(self):
                return Decimal(str(list_to_dict(self.el['value'])['value']))

            def obj_label(self):
                return self._product()['name']

            def obj_code(self):
                code = self._product()['isin']
                # Prefix CFD (Contrats for difference) ISIN codes with "XX-"
                # to avoid id_security duplicates in the database
                if "- CFD" in Field('label')(self):
                    return "XX-" + code
                return code

            def obj_code_type(self):
                if is_isin_valid(Field('code')(self)):
                    return Investment.CODE_TYPE_ISIN
                return NotAvailable

            def _product(self):
                return self.page.browser.get_product(str(Field('_product_id')(self)))

            def parse(self, el):
                currency = self._product()['currency']
                unitvalue = Decimal(str(list_to_dict(self.el['value'])['price']))

                if currency == self.env['currency']:
                    self.env['unitvalue'] = unitvalue
                else:
                    self.env['original_unitvalue'] = unitvalue

                self.env['original_currency'] = currency


class InvestmentPage(LoggedPage, JsonPage):
    def get_products(self):
        return self.doc.get('data', [])


class Transaction(FrenchTransaction):
    PATTERNS = [(re.compile('^(Deposit|Versement)'), FrenchTransaction.TYPE_DEPOSIT),
                (re.compile('^(Buy|Sell|Achat|Vente)'), FrenchTransaction.TYPE_ORDER),
                (re.compile(u'^(?P<text>.*)'), FrenchTransaction.TYPE_BANK),
               ]


class HistoryPage(LoggedPage, JsonPage):
    @method
    class iter_history(DictElement):
        item_xpath = 'data/cashMovements'

        class item(ItemElement):
            klass = Transaction

            obj_raw = Transaction.Raw(CleanText(Dict('description')))
            obj_date = Date(CleanText(Dict('date')), dayfirst=True)
            obj__isin = Regexp(Dict('description'), r'\((.{12}?)\)', nth=-1, default=None)
            obj__number = Regexp(Dict('description'), r'^([Aa]chat|[Vv]ente|[Bb]uy|[Ss]ell) (\d+[,.]?\d*)', template='\\2', default=None)
            obj__datetime = Dict('date')

            def obj_id(self):
                date = CleanText(Dict('date'))(self).split('+')[0]
                date = datetime.datetime.strptime(date, '%Y-%m-%dT%H:%M:%S')
                _id = '%s_%s' % (CleanDecimal(Dict('id'))(self), date)
                return _id

            def obj__action(self):
                if not Field('_isin')(self):
                    return

                label = Field('raw')(self).split()[0]
                return {
                    'Buy': 'B',
                    'Achat': 'B',
                    'Compra': 'B',
                    'Sell': 'S',
                    'Vente': 'S',
                    'Venta': 'S',
                    'Venda': 'S',
                    'Taxe': None,
                    'Frais': None,
                    'Intérêts': None,
                    'Comisión': None,
                    'Custo': None,
                    'DEGIRO': None,
                    # make sure we don't miss transactions labels specifying an ISIN
                }[label]

            def obj_investments(self):
                tr_investment_list = Env('transaction_investments')(self).v
                isin = Field('_isin')(self)
                action = Field('_action')(self)
                if isin and action:
                    tr_inv_key = (isin, action, Field('_datetime')(self))
                    try:
                        return [tr_investment_list[tr_inv_key]]
                    except KeyError:
                        pass
                return []

            def obj_amount(self):
                # The investment "Conversion Cash Fund" doesn't have any
                # 'change' key. But quantity and unit value can be found
                # in the label
                try:
                    return CleanDecimal(Dict('change'))(self)
                except ParseError:
                    pattern = r"[\s\d,]+@[\s\d,]+"
                    select_raw = Field('raw')
                    try:
                        match = Regexp(select_raw, pattern)(self)
                    # some operations don't seem to have any amount
                    # ex: "Variation Cash Fund"
                    except RegexpError:
                        return NotAvailable
                    quantity, unitprice = [
                        CleanDecimal(replace_dots=True).filter(part)
                        for part in match.split('@')
                    ]
                    amount = quantity * unitprice
                    raw = select_raw(self).lower()
                    if any(i for i in ('vente', 'venta', 'venda', 'sell') if i in raw):
                        return amount
                    if any(i for i in ('achat', 'compra', 'buy') if i in raw):
                        return -amount

    @method
    class iter_transaction_investments(DictElement):
        item_xpath = 'data'

        class item(ItemElement):
            klass = Investment

            obj__product_id = Dict('productId')
            obj_quantity = CleanDecimal(Dict('quantity'))
            obj_unitvalue = CleanDecimal(Dict('price'))
            obj_vdate = Date(CleanText(Dict('date')), dayfirst=True)
            obj__action = Dict('buysell')

            obj__datetime = Dict('date')

            def _product(self):
                return self.page.browser.get_product(str(Field('_product_id')(self)))

            def obj_label(self):
                return self._product()['name']

            def obj_code(self):
                code = self._product()['isin']
                # Prefix CFD (Contrats for difference) ISIN codes with "XX-"
                # to avoid id_security duplicates in the database
                if "- CFD" in Field('label')(self):
                    return "XX-" + code
                return code

            def obj_code_type(self):
                if is_isin_valid(Field('code')(self)):
                    return Investment.CODE_TYPE_ISIN
                return NotAvailable

    def get_products(self):
        return set(d['productId'] for d in self.doc['data'])
