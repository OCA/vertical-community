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


from openerp import netsvc
from openerp import pooler
from openerp import SUPERUSER_ID
from openerp.osv import fields, osv, orm
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp

import logging
#_logger = logging.getLogger(__name__)



class mail_group(osv.osv):

    _inherit = 'mail.group'

    _columns = {
        'partner_wallet_ids': fields.many2many('res.partner', 'mail_group_partner_wallets', 'group_id', 'partner_id', 'Partners Wallet', readonly=True),
    }



class account_centralbank_transaction(osv.osv):

    _inherit = 'account.centralbank.transaction'

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        res = super(account_centralbank_transaction, self)._get_user_role(cr, uid, ids, prop, unknow_none, context=context)
        wf_service = netsvc.LocalService("workflow")
        partner_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).partner_id.id
        #_logger.info('res init %s', res)
        #_logger.info('partner_id %s', partner_id)
        for transaction in self.browse(cr, uid, ids, context=context):
            #_logger.info(' wallet_ids %s', transaction.sender_id.group_id and transaction.sender_id.group_id.partner_wallet_ids or False)
            if transaction.sender_id.group_id and partner_id in [p.id for p in transaction.sender_id.group_id.partner_wallet_ids]:
                res[transaction.id]['is_sender'] = True
            if transaction.receiver_id.group_id and partner_id in [p.id for p in transaction.receiver_id.group_id.partner_wallet_ids]:
                res[transaction.id]['is_receiver'] = True
        #_logger.info('res %s', res)
        return res

    _columns = {
        'is_sender': fields.function(_get_user_role, type="boolean", string="Is sender?", multi='role'),
        'is_receiver': fields.function(_get_user_role, type="boolean", string="Is receiver?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
    }
