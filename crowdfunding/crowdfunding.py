# -*- coding: utf-8 -*-
##############################################################################
#
#    Author: Yannick Buron
#    Copyright 2013 Yannick Buron
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

import openerp.addons.decimal_precision as dp

from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
from datetime import datetime
import base64

import logging
_logger = logging.getLogger(__name__)



class crowdfunding_campaign(osv.AbstractModel):

    _name = 'crowdfunding.campaign'
    _description = 'Campaign'


    def _get_price_name(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for campaign in self.browse(cr, uid, ids, context=context):
            res[campaign.id] = ''
        return res

    def _get_funded(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for campaign in self.browse(cr, uid, ids, context=context):
            res[campaign.id] = ''
        return res


    _columns = {
        'crowdfunding': fields.boolean('Launch a crowdfunding campaign?'),
        'crowdfunding_description': fields.text('Crowdfunding description'),
        'crowdfunding_currency_mode': fields.selection([('one','Only one currency'),('all','All currency')], 'Currency mode', required=True, help="Specify the currency mode, if you select one then you'll get the currency when a goal for one currency if attein but you'll lose all other currency. If you select all, you must atteign each goal for each currency but you'll win all the currency"),
        'crowdfunding_date_limit': fields.datetime('Limit date'),
        'crowdfunding_total': fields.function(_get_price_name, string='Total', type="char", size=64, digits_compute= dp.get_precision('Account'), store=True, readonly=True),
        'crowdfunding_currency_ids': fields.one2many('account.centralbank.currency.line', 'res_id',
            domain=lambda self: [('model', '=', self._name),('field','=','crowdfunding_currency_ids')],
            auto_join=True,
            string='Currencies'),
        'crowdfunding_reward_ids': fields.one2many('crowdfunding.reward', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Rewards'),
        'crowdfunding_transaction_ids': fields.one2many('crowdfunding.transaction', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Transactions'),
        'crowdfunding_funded': fields.function(_get_funded, string="Funded?", type="boolean", store=True, readonly=True),
        'crowdfunding_state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('done','Closed'),
            ('cancel','Cancelled'),
            ],'Status', readonly=True, required=True),
    }

    _defaults = {
        'crowdfunding_currency_mode': 'one',
        'crowdfunding_state': 'draft'
    }

class crowdfunding_reward(osv.osv):

    _name = 'crowdfunding.reward'
    _description = 'Reward'


    def _get_price_name(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for reward in self.browse(cr, uid, ids, context=context):
            res[reward.id] = ''
        return res

    def _get_qty_available(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for reward in self.browse(cr, uid, ids, context=context):
            res[reward.id] = ''
        return res


    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'name': fields.char('Name', size=128, required=True),
        'description': fields.text('Description'),
        'total': fields.function(_get_price_name, string='Total', type="char", size=64, digits_compute= dp.get_precision('Account'), store=True, readonly=True),
        'currency_ids': fields.one2many('account.centralbank.currency.line', 'res_id',
            domain=lambda self: [('model', '=', self._name),('field','=','currency_ids')],
            auto_join=True,
            string='Currencies'),
        'quantity': fields.integer('Quantity'),
        'quantity_available': fields.function(_get_qty_available, type="integer", string="Available", readonly=True),
        'partner_ids': fields.many2many('res.partner', 'crowdfunding_reward_partner_rel', 'reward_id', 'partner_id', 'Partners'),
    }

class crowdfunding_transaction(osv.osv):

    _name = 'crowdfunding.transaction'
    _description = 'Transaction'
    _inherits = {'account.centralbank.transaction': "transaction_id"}
    _order = "create_date desc"
    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'crowfunding_transfer_anyway': fields.boolean('The receiver will be able to get the currency even without atteigning the goal'),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('confirm','Confirm'),
            ('paid','Paid'),
            ('confirm_refund','Refund payment confirmation'),
            ('cancel','Cancelled')], readonly=True, required=True),
    }

    def _default_model(self, cr, uid, context=None):

        proxy = self.pool.get('ir.model.data')
        result = proxy.get_object_reference(cr, uid, 'crowdfunding', 'model_crowdfunding_transaction')
        return result[1]

    _defaults = {
        'model_id': _default_model,
    }


