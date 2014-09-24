# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Buron. Copyright Yannick Buron
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import logging
from datetime import datetime

from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
from openerp import workflow
from openerp.tools.translate import _

import openerp.addons.decimal_precision as dp


class CommunityConfigSettings(osv.osv):

    """
    Add currencies configuration to community settings
    """

    _inherit = 'community.config.settings'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Community Journal', required=True),
        'currency_ids': fields.one2many('account.wallet.config.currency', 'config_id', 'Currencies'),
        'default_currency_id': fields.many2one('res.currency', 'Default currency', 
                                               domain=[('wallet_currency', '=', True)], required=True),
    }

    #TODO
    #Try to remove warning at module loading, but not working since xml is loaded after the table modification
    # _defaults = {
    #     'journal_id': lambda s,cr,uid,c: s.pool.get('ir.model.data').get_object(cr, uid, 
    #                           'account_wallet', 'community_journal').id,
    #     'default_currency_id': lambda s,cr,uid,c: s.pool.get('ir.model.data').get_object(cr, uid, 
    #                           'account_wallet', 'COM').id
    # }


class AccountWalletConfigCurrency(osv.osv):

    """
    Lines containing the general configuration for wallet currencies
    """

    _name = 'account.wallet.config.currency'
    _columns = {
        'config_id': fields.many2one('community.config.settings', 'Config', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute=dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute=dp.get_precision('Product Price')),
        'partner_availability_account_id': fields.many2one('account.account',
                                                           'Partner Availability account', required=True),
        'partner_reserved_account_id': fields.many2one('account.account', 'Partner Reserved account', required=True),
        'partner_expense_account_id': fields.many2one('account.account', 'Partner Expense account', required=True),
        'partner_income_account_id': fields.many2one('account.account', 'Partner Income account', required=True),
        'external_currency': fields.boolean('External currency'),
    }

    _sql_constraints = [
        ('currency', 'unique(currency_id)', 'We can only have one line per currency')
    ]

    def update_all_partners(self, cr, uid, context=None):
        #Update balances on all partners
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [], context=context)
        partner_obj.update_wallet_balance(cr, uid, partner_ids, context=context)

    def create(self, cr, uid, vals, context=None):
        #Mark the currency as wallet and then update balance on all partners at creation
        self.pool.get('res.currency').write(cr, uid, [vals['currency_id']], {'wallet_currency': True}, context=context)
        res = super(AccountWalletConfigCurrency, self).create(cr, uid, vals, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        #Update balance on all partners when modified
        res = super(AccountWalletConfigCurrency, self).write(cr, uid, ids, vals, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        #Remove the wallet flag on the currency and then update balance on all partners
        for currency in self.browse(cr, uid, ids, context=context):
            self.pool.get('res.currency').write(cr, uid, [currency.currency_id.id],
                                                {'wallet_currency': False}, context=context)
        res = super(AccountWalletConfigCurrency, self).unlink(cr, uid, ids, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res