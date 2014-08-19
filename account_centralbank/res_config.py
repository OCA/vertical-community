# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (C) 2004-2012 OpenERP S.A. (<http://openerp.com>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import logging
#_logger = logging.getLogger(__name__)


class community_config_settings(osv.osv):
    _inherit = 'community.config.settings'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Community Journal', required=True), #TODO Move in config currency?
#        'group_commission': fields.boolean('Group can define commission'), #TODO move in marketplace_groups module
        'currency_ids': fields.one2many('account.centralbank.config.currency', 'config_id', 'Currencies'),
        'default_currency_id': fields.many2one('res.currency', 'Default currency', domain=[('centralbank_currency', '=', True)], required=True),
    }

class account_centralbank_config_currency(osv.osv):
    _name = 'account.centralbank.config.currency'

    _columns = {
        'config_id': fields.many2one('community.config.settings', 'Config', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute= dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute= dp.get_precision('Product Price')),
        'partner_availability_account_id': fields.many2one('account.account', 'Partner Availability account', required=True),
        'partner_reserved_account_id': fields.many2one('account.account', 'Partner Reserved account', required=True),
        'partner_expense_account_id': fields.many2one('account.account', 'Partner Expense account', required=True),
        'partner_income_account_id': fields.many2one('account.account', 'Partner Income account', required=True),
        'external_currency': fields.boolean('External currency'),
    }

    def update_all_partners(self, cr, uid, context=None):
        partner_obj = self.pool.get('res.partner')
        partner_ids = partner_obj.search(cr, uid, [], context=context)
        partner_obj.update_centralbank_balance(cr, uid, partner_ids, context=context)

    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.currency').write(cr, uid, [vals['currency_id']], {'centralbank_currency': True}, context=context)
        res = super(account_centralbank_config_currency, self).create(cr, uid, vals, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        res = super(account_centralbank_config_currency, self).write(cr, uid, ids, vals, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        for currency in self.browse(cr, uid, ids, context=context):
            self.pool.get('res.currency').write(cr, uid, [currency.currency_id.id], {'centralbank_currency': False}, context=context)
        res = super(account_centralbank_config_currency, self).unlink(cr, uid, ids, context=context)
        self.update_all_partners(cr, uid, context=context)
        return res




# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
