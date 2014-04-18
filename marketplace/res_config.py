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
_logger = logging.getLogger(__name__)


class marketplace_config_settings(osv.osv):
    _name = 'marketplace.config.settings'
    _description = 'Marketplace configuration'
#    _inherit = 'res.config.settings'

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Marketplace Journal', required=True),
#        'community_currency_id': fields.many2one('res.currency', 'Community currency', required=True),
#        'community_partner_availability_account_id': fields.many2one('account.account', 'Marketplace community partner availability account', required=True),
#        'community_partner_reserved_account_id': fields.many2one('account.account', 'Marketplace community partner reserved account', required=True),
#        'community_partner_expense_account_id': fields.many2one('account.account', 'Marketplace community partner expense account', required=True),
#        'community_partner_income_account_id': fields.many2one('account.account', 'Marketplace community partner income account', required=True),
#        'community_company_stock_account_id': fields.many2one('account.account', 'Marketplace community company stock account', required=True),
#        'community_company_availability_account_id': fields.many2one('account.account', 'Marketplace community company availability account', required=True),
#        'community_company_reserved_account_id': fields.many2one('account.account', 'Marketplace community company reserved account', required=True),
#        'community_company_expense_account_id': fields.many2one('account.account', 'Marketplace community company expense account', required=True),
#        'community_company_income_account_id': fields.many2one('account.account', 'Marketplace community company income account', required=True),
#        'real_currency_id': fields.many2one('res.currency', 'Real currency', required=True),
#        'real_partner_availability_account_id': fields.many2one('account.account', 'Marketplace real partner availability account', required=True),
#        'real_partner_reserved_account_id': fields.many2one('account.account', 'Marketplace real partner reserved account', required=True),
#        'real_partner_expense_account_id': fields.many2one('account.account', 'Marketplace real partner expense account', required=True),
#        'real_partner_income_account_id': fields.many2one('account.account', 'Marketplace real partner income account', required=True),
#        'real_company_availability_account_id': fields.many2one('account.account', 'Marketplace real company availability account', required=True),
#        'real_company_reserved_account_id': fields.many2one('account.account', 'Marketplace real company reserved account', required=True),
#        'real_company_expense_account_id': fields.many2one('account.account', 'Marketplace real company expense account', required=True),
#        'real_company_income_account_id': fields.many2one('account.account', 'Marketplace real company income account', required=True),
#        'community_percent_company': fields.float('% Community for company', digits_compute= dp.get_precision('Product Price')),
#        'real_percent_company': fields.float('% Real for company', digits_compute= dp.get_precision('Product Price')),
        'currency_ids': fields.one2many('marketplace.config.currency', 'config_id', 'Currencies'),
        'default_currency_id': fields.many2one('res.currency', 'Default currency', domain=[('marketplace_currency', '=', True)], required=True),
        'group_commission': fields.boolean('Group can define commission'), #TODO move in marketplace_groups module
    }


#    def get_default_config_settings(self, cr, uid, fields, context=None):
#        res = {}
#        res['journal_id'] = int(self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_journal_id'))
#        res['community_currency_id'] = int(self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_currency_id'))
#        res['community_partner_availability_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_community_partner_availability_account', 'res.partner', context=context).id
#        res['community_partner_reserved_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_community_partner_reserved_account', 'res.partner', context=context).id
#        res['community_partner_expense_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_community_partner_expense_account', 'res.partner', context=context).id
#        res['community_partner_income_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_community_partner_income_account', 'res.partner', context=context).id
#        res['community_company_stock_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_company_stock_account_id')
#        res['community_company_availability_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_company_availability_account_id')
#        res['community_company_reserved_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_company_reserved_account_id')
#        res['community_company_expense_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_company_expense_account_id')
#        res['community_company_income_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_company_income_account_id')
#        res['real_currency_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_currency_id')
#        res['real_partner_availability_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_real_partner_availability_account', 'res.partner', context=context).id
#        res['real_partner_reserved_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_real_partner_reserved_account', 'res.partner', context=context).id
#        res['real_partner_expense_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_real_partner_expense_account', 'res.partner', context=context).id
#        res['real_partner_income_account_id'] = self.pool.get('ir.property').get(cr, uid, 'property_marketplace_real_partner_income_account', 'res.partner', context=context).id
#        res['real_company_availability_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_company_availability_account_id')
#        res['real_company_reserved_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_company_reserved_account_id')
#        res['real_company_expense_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_company_expense_account_id')
#        res['real_company_income_account_id'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_company_income_account_id')
#        res['community_percent_company'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_percent_company')
#        res['real_percent_company'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_percent_company')
#        res['group_commission'] = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_group_commission')

#        currency_obj = self.pool.get('marketplace.currency')
#        currency_ids = currency_obj.search(cr, uid, [], context=context)
#        res['currency_ids'] = []
#        for currency in currency_obj.browse(cr, uid, currency_ids, context=context):
#            res_currency = {}
#            res_currency['currency_id'] = currency.currency_id.id
#            res_currency['partner_availability_account_id'] = currency.partner_availability_account_id.id,
#            res_currency['partner_reserved_account_id'] = currency.partner_reserved_account_id.id,
#            res_currency['partner_expense_account_id'] = currency.partner_expense_account_id.id,
#            res_currency['partner_income_account_id'] = currency.partner_income_account_id.id,
#            res_currency['company_availability_account_id'] = currency.company_availability_account_id.id,
#            res_currency['company_reserved_account_id'] = currency.company_reserved_account_id.id,
#            res_currency['company_expense_account_id'] = currency.company_expense_account_id.id,
#            res_currency['company_income_account_id'] = currency.company_income_account_id.id,
#            _logger.info('Res_currency: %s', res_currency)
#            res['currency_ids'].append(res_currency)
#        _logger.info('Res: %s', res)
#        return res

#    def set_settings(self, cr, uid, ids, context=None):
#        _logger.info('test')
#        config = self.browse(cr, uid, ids)[0]
#        property_obj = self.pool.get('ir.property')
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_journal_id', config.journal_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_currency_id', config.community_currency_id.id)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_community_partner_availability_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.community_partner_availability_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_community_partner_reserved_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.community_partner_reserved_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_community_partner_expense_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.community_partner_expense_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_community_partner_income_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.community_partner_income_account_id.id)+''}, context=context)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_company_stock_account_id', config.community_company_stock_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_company_availability_account_id', config.community_company_availability_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_company_reserved_account_id', config.community_company_reserved_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_company_expense_account_id', config.community_company_expense_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_company_income_account_id', config.community_company_income_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_currency_id', config.real_currency_id.id)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_real_partner_availability_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.real_partner_availability_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_real_partner_reserved_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.real_partner_reserved_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_real_partner_expense_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.real_partner_expense_account_id.id)+''}, context=context)
#        account_property_id = property_obj.search(cr,uid,[('name','=','property_marketplace_real_partner_income_account'),('res_id','=',False)])
#        property_obj.write(cr, uid, account_property_id, {'value':'account.account,'+str(config.real_partner_income_account_id.id)+''}, context=context)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_company_availability_account_id', config.real_company_availability_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_company_reserved_account_id', config.real_company_reserved_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_company_expense_account_id', config.real_company_expense_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_company_income_account_id', config.real_company_income_account_id.id)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_community_percent_company', config.community_percent_company)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_real_percent_company', config.real_percent_company)
#        self.pool.get('ir.config_parameter').set_param(cr,uid, 'marketplace_group_commission', config.group_commission)

#        currency_obj = self.pool.get('marketplace.currency')
#        for currency in config.currency_ids:
#            vals = {}
#            vals['currency_id'] = currency.currency_id.id
#            vals['partner_availability_account_id'] = currency.partner_availability_account_id.id
#            vals['partner_reserved_account_id'] = currency.partner_reserved_account_id.id
#            vals['partner_expense_account_id'] = currency.partner_expense_account_id.id
#            vals['partner_income_account_id'] = currency.partner_income_account_id.id
#            vals['company_availability_account_id'] = currency.company_availability_account_id.id
#            vals['company_reserved_account_id'] = currency.company_reserved_account_id.id
#            vals['company_expense_account_id'] = currency.company_expense_account_id.id
#            vals['company_income_account_id'] = currency.company_income_account_id.id
#            _logger.info('test')
#            _logger.info('Vals: %s', vals)
#
#            currency_ids = currency_obj.search(cr, uid, [('currency_id', '=', currency.currency_id.id)], context=context)
#            if currency_ids:
#                currency_obj.write(cr, uid, currency_ids, vals, context=context)
#            else:
#                currency_obj.create(cr, uid, vals, context=context)
#        return True

class marketplace_config_currency(osv.osv):
    _name = 'marketplace.config.currency'

    _columns = {
        'config_id': fields.many2one('marketplace.config.settings', 'Config', required=True),
        'currency_id': fields.many2one('res.currency', 'Real currency', required=True),
        'limit': fields.float('Limit', digits_compute= dp.get_precision('Product Price')),
        'partner_availability_account_id': fields.many2one('account.account', 'Marketplace partner availability account', required=True),
        'partner_reserved_account_id': fields.many2one('account.account', 'Marketplace partner reserved account', required=True),
        'partner_expense_account_id': fields.many2one('account.account', 'Marketplace partner expense account', required=True),
        'partner_income_account_id': fields.many2one('account.account', 'Marketplace partner income account', required=True),
        'company_availability_account_id': fields.many2one('account.account', 'Marketplace company availability account', required=True),
        'company_reserved_account_id': fields.many2one('account.account', 'Marketplace company reserved account', required=True),
        'company_expense_account_id': fields.many2one('account.account', 'Marketplace company expense account', required=True),
        'company_income_account_id': fields.many2one('account.account', 'Marketplace company income account', required=True),
        'percent_company': fields.float('% for company', digits_compute= dp.get_precision('Product Price')),
        'external_currency': fields.boolean('External currency'),
    }

    def create(self, cr, uid, vals, context=None):
        self.pool.get('res.currency').write(cr, uid, [vals['currency_id']], {'marketplace_currency': True}, context=context)
        return super(marketplace_config_currency, self).create(cr, uid, vals, context=context)

    def unlink(self, cr, uid, ids, context=None):
        for currency in self.browse(cr, uid, ids, context=context):
            self.pool.get('res.currency').write(cr, uid, [currency.currency_id.id], {'marketplace_currency': False}, context=context)
        return super(marketplace_config_currency, self).unlink(cr, uid, ids, context=context)



#class marketplace_currency(osv.osv):
#    _name = 'marketplace.currency'

#    _columns = {
#        'currency_id': fields.many2one('res.currency', 'Real currency', required=True),
#        'partner_availability_account_id': fields.many2one('account.account', 'Marketplace partner availability account', required=True),
#        'partner_reserved_account_id': fields.many2one('account.account', 'Marketplace partner reserved account', required=True),
#        'partner_expense_account_id': fields.many2one('account.account', 'Marketplace partner expense account', required=True),
#        'partner_income_account_id': fields.many2one('account.account', 'Marketplace partner income account', required=True),
#        'company_availability_account_id': fields.many2one('account.account', 'Marketplace company availability account', required=True),
#        'company_reserved_account_id': fields.many2one('account.account', 'Marketplace company reserved account', required=True),
#        'company_expense_account_id': fields.many2one('account.account', 'Marketplace company expense account', required=True),
#        'company_income_account_id': fields.many2one('account.account', 'Marketplace company income account', required=True),
#    }


class vote_config_settings(osv.osv):
    _inherit = 'vote.config.settings'

    def write(self, cr, uid, ids, vals, context=None):
        res = super(vote_config_settings, self).write(cr, uid, ids, vals, context=context)

        for config in self.browse(cr, uid, ids, context=context):
            model_obj = self.pool.get('marketplace.announcement.category') 
            model_ids = model_obj.search(cr, uid, [('parent_id', '=', False)], context=context)
            model_obj._update_stored_vote_config(cr, uid, model_ids, context=context)
        return res

vote_config_settings()


# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
