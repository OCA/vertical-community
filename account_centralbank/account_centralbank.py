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


class account_centralbank_currency_line(osv.osv):

    _name = 'account.centralbank.currency.line'
    _description = 'Currency line'

    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for currency in self.browse(cr, uid, ids, context=context):
            model_obj = self.pool.get(currency.model)
            transaction = model_obj.browse(cr, uid, currency.res_id, context=context)
            res[currency.id] = 1.0
            if transaction:
                res[currency.id] = transaction.quantity * currency.price_unit
        return res


    _columns = {
        'model': fields.char('Related Document Model', size=128, select=1),
        'res_id': fields.integer('Related Document ID', select=1),
        'price_unit': fields.float('Unit price', required=True, digits_compute= dp.get_precision('Product Price')),
        'currency_id': fields.many2one('res.currency', 'Currency', domain=[('centralbank_currency', '=', True)], required=True),
        'subtotal': fields.function(_get_subtotal, string='Subtotal', digits_compute= dp.get_precision('Account')),
    }


class account_centralbank_transaction(osv.osv):

    def _get_price_name(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        wf_service = netsvc.LocalService("workflow")
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [], context=context)
        company_name = company_obj.browse(cr, uid, company_ids, context=context)[0].name
        for proposition in self.browse(cr, uid, ids, context=context):
            res[proposition.id] = ''
            for currency in proposition.currency_ids:
                if res[proposition.id] != '':
                    res[proposition.id] += ', '
                res[proposition.id] += str(currency.subtotal) + ' ' + currency.currency_id.symbol
        return res


    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        wf_service = netsvc.LocalService("workflow")
        res = {}
        partner_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).partner_id.id 
        for transaction in self.browse(cr, uid, ids, context=context):
            res[transaction.id] = {}
            res[transaction.id]['is_sender'] = False
            res[transaction.id]['is_receiver'] = False
            res[transaction.id]['is_moderator'] = False
            _logger.info('user_ids %s', transaction.sender_id.user_ids)
            if transaction.sender_id.id == partner_id:
                res[transaction.id]['is_sender'] = True
            if transaction.receiver_id.id == partner_id:
                res[transaction.id]['is_receiver'] = True
            if self.pool.get('res.users').has_group(cr, uid, 'account_centralbank.group_account_centralbank_moderator'):
                res[transaction.id]['is_sender'] = True
                res[transaction.id]['is_receiver'] = True
                res[transaction.id]['is_moderator'] = True
        return res


    _name = 'account.centralbank.transaction'
    _description = 'Transaction'
    _inherit = ['mail.thread']
    _order = "create_date desc"
    _columns = {
        'sender_id': fields.many2one('res.partner', 'Sender', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'receiver_id': fields.many2one('res.partner', 'Receiver', required=True, readonly=True, states={'draft':[('readonly',False)]}),
        'description': fields.text('Detail'),
        'total': fields.function(_get_price_name, string='Total', type="char", size=64, digits_compute= dp.get_precision('Account'), store=True, readonly=True),
        'quantity': fields.float('Exchanged quantity', digits_compute= dp.get_precision('Product Unit of Measure')),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
        'currency_ids': fields.one2many('account.centralbank.currency.line', 'res_id',
            domain=lambda self: [('model', '=', self._name)],
            auto_join=True,
            string='Currencies', readonly=True, states={'draft':[('readonly',False)]}),
        'move_ids': fields.one2many('account.move', 'centralbank_transaction_id', 'Moves'),
        'reservation_id': fields.many2one('account.move', 'Reservation move'),
        'invoice_id': fields.many2one('account.move', 'Invoice move'),
        'payment_id': fields.many2one('account.move', 'Payment move'),
        'confirm_id': fields.many2one('account.move', 'Confirmation move'),
        'is_sender': fields.function(_get_user_role, type="boolean", string="Is sender?", multi='role'),
        'is_receiver': fields.function(_get_user_role, type="boolean", string="Is receiver?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'state': fields.selection([
            ('draft','Draft'),
            ('confirm','Confirm'),
            ('done','Closed'),
            ('confirm_refund','Confirm Refund'), 
            ('cancel','Cancelled'),
            ],'Status', readonly=True, required=True),

    }

    def _default_partner(self, cr, uid, context=None):

        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.partner_id.id


    def _default_currency_ids(self, cr, uid, context=None):
        if context is None:
            context = {}
        currency_ids = []
        if context.get('default_announcement_id'):
            for currency in self.pool.get('marketplace.announcement').browse(cr, uid, [context.get('default_announcement_id')], context=context)[0].currency_ids:
                vals = {}
                vals['price_unit'] = currency.price_unit
                vals['currency_id'] = currency.currency_id.id
                vals['company_commission'] = currency.company_commission
                currency_ids.append((0, 0, vals))
        return currency_ids

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    _defaults = {
        'state': 'draft',
        'currency_ids': _default_currency_ids,
        'quantity': 1.0,
        'uom_id': _get_uom_id,
        'sender_id': _default_partner,
    }

    def test_access_role(self, cr, uid, ids, role_to_test, *args):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test')

        res = self._get_user_role(cr, uid, ids, {}, {})

        for transaction in self.browse(cr, uid, ids):
            role = res[transaction.id]
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('Role : %s, role to test : %s', role, role_to_test)

            if not role[role_to_test]:
                raise osv.except_osv(_('Access error!'),_("You need to have the role " + role_to_test + " to perform this action!"))
        return True


    def reconcile(self, cr, uid, move_ids, context=None):
        account_obj = self.pool.get('account.account')
        move_obj = self.pool.get('account.move')
        move_line_obj = self.pool.get('account.move.line')

        res = {}
        for move in move_obj.browse(cr, uid, move_ids, context=context):
            for line in move.line_id:
                move_line_obj._remove_move_reconcile(cr, uid, [line.id], context=context)
                if not line.account_id.id in res:
                    res[line.account_id.id] = {}
                if not line.partner_id.id in res[line.account_id.id]:
                    res[line.account_id.id][line.partner_id.id] = {}
                    res[line.account_id.id][line.partner_id.id]['total_debit'] = 0.0
                    res[line.account_id.id][line.partner_id.id]['total_credit'] = 0.0
                    res[line.account_id.id][line.partner_id.id]['line_ids'] = []
                res[line.account_id.id][line.partner_id.id]['total_debit'] += line.debit
                res[line.account_id.id][line.partner_id.id]['total_credit'] += line.credit
                res[line.account_id.id][line.partner_id.id]['line_ids'].append(line.id)
        for account_id, res_account in res.iteritems():
            account = account_obj.browse(cr, uid, [account_id], context=context)[0]
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('res_account: %s', res_account)
            for partner_id, res_partner in res_account.iteritems():
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('res_partner: %s, reconcile %s', res_partner, account.reconcile)
                if res_partner['total_debit'] == res_partner['total_credit'] and account.reconcile:
                     move_line_obj.reconcile(cr, uid, res_partner['line_ids'], context=context)

    def refund(self, cr, uid, ids, fields, obj, context=None):

        pool = self.pool.get(obj)
        move_obj = self.pool.get('account.move')
        date = datetime.now().strftime("%Y-%m-%d")

        for transaction in pool.browse(cr, uid, ids, context=context):

            for move_field in fields:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('Move field: %s', getattr(transaction, move_field + '_id'))

                move = getattr(transaction, move_field + '_id')
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('Move %s', move)

#                if getattr(proposition, move_field + '_id'):
                if move:
                    flag = 'cancel_' + move_field
                    reversal_move_id = move_obj.create_reversals(cr, uid, [move.id], date)[0]
                    import logging
                    _logger = logging.getLogger(__name__)
                    _logger.info('Reversal moveid : %s', reversal_move_id)
                    move_obj.post(cr, uid, [reversal_move_id])
                    move_obj.write(cr, uid, [reversal_move_id], {'centralbank_action': flag, 'centralbank_transaction_id': transaction.id}, context=context)
                    self.write(cr, uid, [transaction.id], {move_field + '_id': False}, context=context)
                    self.reconcile(cr, uid, [move.id, reversal_move_id], context=context)

    def control_amount(self, cr, uid, transaction, sender, receiver, inv=False, context=None):

        partner_obj = self.pool.get('res.partner')

        if inv:
            temp_sender = sender
            sender = receiver
            receiver = temp_sender

        balance = partner_obj.get_centralbank_balance(cr, uid, [sender.id])[sender.id]
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('balance : %s, sender: %s', balance, sender)
        for currency in transaction.currency_ids:
            balance_currency = balance[currency.currency_id.id]
            if balance_currency['limit_negative'] and (balance_currency['available'] - currency.subtotal) < balance_currency['limit_negative_value']:
                raise osv.except_osv(_('Limit error!'),_("Not enough amount available for %s. Currency : %s, Current : %s, Needed : %s, Limit : %s") % (sender.name, currency.currency_id.symbol, balance_currency['available'], currency.subtotal, balance_currency['limit_negative_value']))

        balance = partner_obj.get_centralbank_balance(cr, uid, [receiver.id])[receiver.id]
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('balance : %s, receiver: %s', balance, receiver)
        for currency in transaction.currency_ids:
            balance_currency = balance[currency.currency_id.id]
            if balance_currency['limit_positive'] and (balance_currency['available'] - currency.subtotal) > balance_currency['limit_positive_value']:
                raise osv.except_osv(_('Limit error!'),_("Too much amount available for %s. Currency : %s, Current %s, Needed : %s, Limit : %s") % (receiver.name, currency.currency_id.symbol, balance_currency['available'], currency.subtotal, balance_currency['limit_positive_value']))



    def get_account_line(self, cr, uid, transaction, action, action2, deduction=0.0, inv=False, name='Transaction', context=None):

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test get_account_line : %s', action)


        if not inv:
            partner_credit = transaction.sender_id
            partner_debit = transaction.receiver_id
        else:
            partner_credit = transaction.receiver_id
            partner_debit = transaction.sender_id

        if action == 'reservation':
            self.control_amount(cr, uid, transaction, transaction.sender_id, transaction.receiver_id, inv=inv, context=context)
            partner_debit = partner_credit
        if action == 'confirm':
            temp_partner_debit = partner_debit
            partner_debit = partner_credit
            partner_credit = temp_partner_debit


        partner_currency_obj = self.pool.get('res.partner.centralbank.currency')
        config_currency_obj = self.pool.get('account.centralbank.config.currency')

        lines = []
        for currency in transaction.currency_ids:
            diff_currency_p = currency.currency_id.id <> context['company_currency']
            config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id', '=', currency.currency_id.id)], context=context)
            if not config_currency_ids:
                raise osv.except_osv(_('Config error!'),_("One of the currency is missing in the configuration!"))
            config_currency = config_currency_obj.browse(cr, uid, config_currency_ids, context=context)[0]
            debit_availability_account = config_currency.partner_availability_account_id.id
            debit_reserved_account = config_currency.partner_reserved_account_id.id
            debit_expense_account = config_currency.partner_expense_account_id.id
            debit_income_account = config_currency.partner_income_account_id.id
            credit_availability_account = config_currency.partner_availability_account_id.id
            credit_reserved_account = config_currency.partner_reserved_account_id.id
            credit_expense_account = config_currency.partner_expense_account_id.id
            credit_income_account = config_currency.partner_income_account_id.id

            if action == 'confirm' and not config_currency.external_currency:
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('test %s', config_currency.currency_id.name)

                continue

            partner_currency_ids = partner_currency_obj.search(cr, uid, [('partner_id', '=', partner_debit.id), ('currency_id', '=', currency.currency_id.id)], context=context)
            for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
                if 'availability_account' in partner_currency and partner_currency.availability_account:
                    debit_availability_account = partner_currency.availability_account.id
                if 'reserved_account' in partner_currency and partner_currency.reserved_account:
                    debit_reserved_account = partner_currency.reserved_account.id
                if 'expense_account' in partner_currency and partner_currency.expense_account:
                    debit_expense_account = partner_currency.expense_account.id
                if 'income_account' in partner_currency and partner_currency.income_account:
                    debit_income_account = partner_currency.income_account.id

            partner_currency_ids = partner_currency_obj.search(cr, uid, [('partner_id', '=', partner_credit.id), ('currency_id', '=', currency.currency_id.id)], context=context)
            for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
                if 'availability_account' in partner_currency and partner_currency.availability_account:
                    credit_availability_account = partner_currency.availability_account.id
                if 'reserved_account' in partner_currency and partner_currency.reserved_account:
                    credit_reserved_account = partner_currency.reserved_account.id
                if 'expense_account' in partner_currency and partner_currency.expense_account:
                    credit_expense_account = partner_currency.expense_account.id
                if 'income_account' in partner_currency and partner_currency.income_account:
                    credit_income_account = partner_currency.income_account.id

            currency_id = currency.currency_id.id
            price = currency.subtotal - deduction
            if action == 'reservation':
                account_debit_id = debit_reserved_account
                account_credit_id = credit_availability_account
            elif action == 'invoice':
                account_debit_id = debit_expense_account
                account_credit_id = credit_income_account
            elif action == 'payment':
                account_debit_id = debit_availability_account
                account_credit_id = credit_reserved_account
            elif action == 'confirm':
                account_debit_id = debit_availability_account
                account_credit_id = credit_availability_account

#            if action2 == 'company_com':
#                price = currency.subtotal * config_currency.company_com / 100
#                if action == 'invoice':
#                    account_credit_id = config_currency.company_income_account_id.id
#                elif action == 'payment':
#                    account_debit_id = config_currency.company_availability_account_id.id
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('test1 account_debit_id: %s', account_debit_id)


        #TODO move in groups
        #TODO to finish
#        if action == 'invoice_group_com':
#            if proposition.type == 'offer':
#                partner_debit = proposition.user_id.partner_id
#            else:
#                partner_debit = proposition.announcement_id.user_id.partner_id
#            partner_credit = False
#
#            if currency == 'community':
#                price = proposition.community_price_unit * proposition.quantity * proposition.community_group_com / 100
#                account_debit_id = partner_debit.property_marketplace_community_partner_expense_account.id,
#                account_credit_id = partner_credit.property_marketplace_community_partner_income_account.id,
#            else:
#                price = proposition.real_price_unit * proposition.quantity * proposition.real_group_com / 100
#                account_debit_id = partner_debit.property_marketplace_real_partner_expense_account.id,
#                account_credit_id = partner_credit.property_marketplace_real_partner_income_account.id,
            import logging
            _logger = logging.getLogger(__name__)

            _logger.info('account_debit_id final : %s',account_debit_id)
            lines.append((0,0,{
                    'name': name,
                    'partner_id': partner_debit and partner_debit.id or False,
                    'account_id': account_debit_id,
                    'debit': price,
                    'amount_currency': diff_currency_p and price or False,
                    'currency_id': diff_currency_p and currency_id or False,
                    'quantity': transaction.quantity,
                    'product_uom_id': transaction.uom_id.id,
                }))
            lines.append((0,0,{
                    'name': name,
                    'partner_id': partner_credit and partner_credit.id or False,
                    'account_id': account_credit_id,
                    'credit': price,
                    'amount_currency': diff_currency_p and -price or False,
                    'currency_id': diff_currency_p and currency_id or False,
                    'quantity': transaction.quantity,
                    'product_uom_id': transaction.uom_id.id,
                }))
        return lines


    def prepare_move(self, cr, uid, ids, action, context=None):
        wf_service = netsvc.LocalService("workflow")
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        company_obj = self.pool.get('res.company')
        config = self.pool.get('ir.model.data').get_object(cr, uid, 'base_community', 'community_settings')

        date = datetime.now().date().strftime("%Y-%m-%d")

        context = {}
        company_id = company_obj._company_default_get(cr, uid)
        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id

        for transaction in self.browse(cr, uid, ids, context=context):

            lines = self.get_account_line(cr, uid, transaction, action, 'base', context=context)

            if lines:
                ref = 'Transaction'
                journal_id = config.journal_id.id
                move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
                move['centralbank_transaction_id'] = transaction.id
                move['centralbank_action'] = action
                move_id = move_obj.create(cr, uid, move)

#                if proposition.announcement_id.community_company_commission:
#                    lines = self.get_account_line(cr, uid, lines, proposition, 'community', 'payment', 'company_com', context=context)

            #TODO move in group module
#            if proposition.community_price_unit and proposition.announcement_id.community_group_commission:
#                lines = self.get_account_line(cr, uid, lines, proposition, 'community', 'payment', 'group_com', context=context)
#            if proposition.real_price_unit and proposition.announcement_id.real_company_commission:
#                lines = self.get_account_line(cr, uid, lines, proposition, 'real', 'payment', 'group_com', context=context)

                move_obj.write(cr, uid, [move_id], {'line_id': lines})
                move_obj.post(cr, uid, [move_id])
                self.write(cr, uid, [transaction.id], {action + '_id': move_id})
                if transaction.reservation_id:
                    self.reconcile(cr, uid, [transaction.reservation_id.id, move_id], context=context)


    def get_skip_confirm(self, cr, uid, transaction, context=None):
        config_currency_obj = self.pool.get('account.centralbank.config.currency')

        currency_ids = []
        for currency in transaction.currency_ids:
            currency_ids.append(currency.currency_id.id)
        config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id', 'in', currency_ids)])

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("config_currency_ids : %s", config_currency_ids)


        skip_confirm = True
        for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids):
            if config_currency.external_currency:
                skip_confirm = False
        return skip_confirm

    def confirm(self, cr, uid, ids, *args):
        wf_service = netsvc.LocalService("workflow")
        self.test_access_role(cr, uid, ids, 'is_sender', *args)

        for transaction in self.browse(cr, uid, ids):
            self.prepare_move(cr, uid, [transaction.id], 'reservation')
            self.prepare_move(cr, uid, [transaction.id], 'payment')

            skip_confirm = self.get_skip_confirm(cr, uid, transaction)
            _logger.info('skip_confirm %s', skip_confirm)
            if not skip_confirm:
                wf_service.trg_validate(uid, 'account.centralbank.transaction', transaction.id, 'transaction_draft_confirm', cr)
            else:
                wf_service.trg_validate(uid, 'account.centralbank.transaction', transaction.id, 'transaction_draft_done', cr)
        return True

    def change_state(self, cr, uid, ids, new_state, *args):
        wf_service = netsvc.LocalService("workflow")
        partner_obj = self.pool.get('res.partner')
        for transaction in self.browse(cr, uid, ids):
            fields = {'state':new_state}
            if new_state == 'done':
                self.prepare_move(cr, uid, [transaction.id], 'confirm')
            if new_state == 'cancel':
                self.refund(cr, uid, [transaction.id], ['reservation','invoice','payment','confirm'], 'account.centralbank.transaction')
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('fields : %s', fields)
            self.write(cr, uid, [transaction.id], fields)
        return True

    def reset_workflow(self, cr, uid, ids, *args):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test reset')

        wf_service = netsvc.LocalService("workflow")
        for transaction in self.browse(cr, uid, ids):
            state = transaction.state
            role_to_test = 'is_sender'
            if state == 'done':
                role_to_test = 'is_receiver'
            self.test_access_role(cr, uid, ids, role_to_test, *args)

            wf_service.trg_delete(uid, 'account.centralbank.transaction', transaction.id, cr)
            wf_service.trg_create(uid, 'account.centralbank.transaction', transaction.id, cr)

            if state == 'done':
                skip_confirm = self.get_skip_confirm(cr, uid, transaction)
                _logger.info('skip_confirm %s', skip_confirm)
                if not skip_confirm:
                    wf_service.trg_validate(uid, 'account.centralbank.transaction', transaction.id, 'transaction_done_confirm_refund', cr)
                else:
                    wf_service.trg_validate(uid, 'account.centralbank.transaction', transaction.id, 'transaction_done_cancel', cr)
        return True



class account_move(osv.osv):

    _inherit = 'account.move'

    _columns = {
        'centralbank_transaction_id': fields.many2one('account.centralbank.transaction', 'Transaction'),
        'centralbank_action': fields.selection([
            ('reservation','Reservation'),
            ('invoice','Invoice'),
            ('payment','Payment'),
            ('confirm','Payment confirmation'),
            ('cancel_reservation','Reservation Cancellation'),
            ('cancel_invoice','Refund'),
            ('cancel_payment','Refund Payment'),
            ('cancel_confirm','Payment confirmation cancellation'),
            ],'Type', readonly=True),
    }




class res_partner(osv.osv):

    _inherit = 'res.partner'

    def get_centralbank_limits(self, cr, uid, ids, currency_ids, context=None):

        partner_currency_obj = self.pool.get('res.partner.centralbank.currency')
        config_currency_obj = self.pool.get('account.centralbank.config.currency')

        config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id','in',currency_ids)], context=context)
        config_currency_limits = {}
        for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids, context=context):
            config_currency_limits[config_currency.currency_id.id] = {}
            config_currency_limits[config_currency.currency_id.id]['limit_negative'] = config_currency.limit_negative
            config_currency_limits[config_currency.currency_id.id]['limit_negative_value'] = config_currency.limit_negative_value
            config_currency_limits[config_currency.currency_id.id]['limit_positive'] = config_currency.limit_positive
            config_currency_limits[config_currency.currency_id.id]['limit_positive_value'] = config_currency.limit_positive_value

        partner_currency_ids = partner_currency_obj.search(cr, uid, [('partner_id','in',ids),('currency_id','in',currency_ids)], context=context)
        partner_currency_limits = {}
        for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
            if not partner_currency.partner_id.id in partner_currency_limits:
                partner_currency_limits[partner_currency.partner_id.id] = {}
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id] = {}
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id]['limit_negative'] = partner_currency.limit_negative
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id]['limit_negative_value'] = partner_currency.limit_negative_value
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id]['limit_positive'] = partner_currency.limit_positive
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id]['limit_positive_value'] = partner_currency.limit_positive_value

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = {}
            for currency_id in currency_ids:
                res[partner.id][currency_id] = config_currency_limits[currency_id]
                if partner.id in partner_currency_limits and currency_id in partner_currency_limits[partner.id]:
                    res[partner.id][currency_id] = partner_currency_limits[partner.id][currency_id]

        return res




    def get_centralbank_balance(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        ctx = context.copy()
        ctx['all_fiscalyear'] = True

        company_obj = self.pool.get('res.company')
        company_id = company_obj._company_default_get(cr, uid)
        company_currency_id = company_obj.browse(cr, uid, [company_id])[0].currency_id.id

        config_currency_obj = self.pool.get('account.centralbank.config.currency')
        partner_currency_obj = self.pool.get('res.partner.centralbank.currency')
        config_currency_ids = config_currency_obj.search(cr, uid, [], context=context)
        account_ids = {}
        currency_ids = []
        default_account = {}
        for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids, context=context):
            default_account[config_currency.currency_id.id] = {}
            account_id = config_currency.partner_availability_account_id.id
            account_ids[account_id] = account_id
            default_account[config_currency.currency_id.id]['available'] = account_id
            account_id = config_currency.partner_reserved_account_id.id
            account_ids[account_id] = account_id
            default_account[config_currency.currency_id.id]['reserved'] = account_id
            currency_ids.append(config_currency.currency_id.id)

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info("[('partner_id', 'in', %s), ('currency_id', 'in', %s)]", ids, currency_ids)


        partner_currencies = {}
        partner_currency_ids = partner_currency_obj.search(cr, uid, [('partner_id', 'in', ids), ('currency_id', 'in', currency_ids)], context=context)
        for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
            if not partner_currency.currency_id.id in partner_currencies:
                 partner_currencies[partner_currency.currency_id.id] = {}
            partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id] = {}
            partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id]['available'] = False
            if partner_currency.available_account:
                account_id = partner_currency.available_account.id
                account_ids[account_id] = account_id
                partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id]['available'] = account_id
            partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id]['reserved'] = False
            if partner_currency.reserved_account:
                account_id = partner_currency.reserved_account.id
                account_ids[account_id] = account_id
                partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id]['reserved'] = account_id

        query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('partner_currency %s',partner_currencies)


        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test %s',tuple(account_ids))
#        _logger.info("SELECT l.partner_id, SUM(l.debit-l.credit), l.account_id, a.code FROM account_move_line l LEFT JOIN account_account a ON (l.account_id=a.id) WHERE a.id IN %s AND l.partner_id IN %s AND l.reconcile_id IS NULL AND %s GROUP BY l.partner_id, l.account_id, a.code",tuple(ids),tuple(account_ids)))


        cr.execute("""SELECT l.partner_id, SUM(l.debit-l.credit), l.account_id, l.currency_id, a.code
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE l.partner_id IN %s
                      AND a.id IN %s
                      AND l.reconcile_id IS NULL
                      AND """ + query + """
                      GROUP BY l.partner_id, l.account_id, l.currency_id, a.code
                      """,
                   (tuple(ids),tuple(account_ids)))
        res = {}
        for pid,val,account_id,currency_id,code in cr.fetchall():
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('pid: %s, val : %s, account_id: %s, code:%s',pid,val,account_id,code)
            if not currency_id:
                currency_id = company_currency_id
            if val is None: val=0
            if not currency_id in res:
                res[currency_id] = {}
            if not pid in res[currency_id]:
                res[currency_id][pid] = {}
            res[currency_id][pid][account_id] = val

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('res: %s',res)

        res_final = {}
        partners = self.browse(cr, uid, ids, context=context)

#        import logging
#        _logger = logging.getLogger(__name__)
#        _logger.info('control_partner_ids: %s',control_partner_ids)
        limits = self.get_centralbank_limits(cr, uid, ids, currency_ids, context=context)

        for partner in partners:
            pid = partner.id
            res_final[pid] = {}

            for currency_id in currency_ids:
                vals = {}
                vals['currency_id'] = currency_id
                vals['limit_negative'] = limits[partner.id][currency_id]['limit_negative']
                vals['limit_negative_value'] = limits[partner.id][currency_id]['limit_negative_value']
                vals['limit_positive'] = limits[partner.id][currency_id]['limit_positive']
                vals['limit_positive_value'] = limits[partner.id][currency_id]['limit_positive_value']

                if currency_id in partner_currencies and pid in partner_currencies[currency_id] and 'available' in partner_currencies[currency_id][pid] and partner_currencies[currency_id][pid]['available']:
                    account_id = partner_currencies[currency_id][pid]['available']
                else:
                    account_id = default_account[currency_id]['available']
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('currency_id: %s, pid: %s, account_id: %s',currency_id, pid, account_id)
                vals['available'] = currency_id in res and pid in res[currency_id] and account_id in res[currency_id][pid] and res[currency_id][pid][account_id] or 0.0
                if currency_id in partner_currencies and pid in partner_currencies[currency_id] and 'reserved' in partner_currencies[currency_id][pid] and partner_currencies[currency_id][pid]['reserved']:
                    account_id = partner_currencies[currency_id][pid]['reserved']
                else:
                    account_id = default_account[currency_id]['reserved']
                vals['reserved'] = currency_id in res and pid in res[currency_id] and account_id in res[currency_id][pid] and res[currency_id][pid][account_id] or 0.0
                res_final[pid][currency_id] = vals

        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('res_final: %s',res_final)

        return res_final

    def _get_centralbank_balance(self, cr, uid, ids, field_names, arg, context=None):

        balances = self.get_centralbank_balance(cr, uid, ids, context=context)
        now = datetime.now()
        proxy = self.pool.get('ir.model.data')

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = []

            #In we do not control that the partner already exist, it trigger a bug at the account creation. I am controlling this by checking that the partner wasn't created in the last 60 second, this is crappy but it work. TOIMPROVE TODO
            delta = now - datetime.strptime(partner.create_date,"%Y-%m-%d %H:%M:%S")
            if delta.total_seconds() < 60 or partner.id == proxy.get_object(cr, uid, 'auth_signup', 'default_template_user').partner_id.id:
                continue

            for currency in balances[partner.id].values():
                res[partner.id].append((0,0,currency))
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('res_final: %s',res)

        return res
                


    _columns = {
        'centralbank_currency_ids': fields.one2many('res.partner.centralbank.currency', 'partner_id', 'Currencies'),
        'centralbank_balance_ids': fields.function(_get_centralbank_balance, type="one2many", relation="res.partner.centralbank.balance",string='Balances'),
        'create_date': fields.datetime('Create date'),
    }
#TODO : make store functions

class res_partner_centralbank_currency(osv.osv):

    _name = "res.partner.centralbank.currency"
    _description = "Currency"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', domain=[('centralbank_currency', '=', True)], required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute= dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute= dp.get_precision('Product Price')),
        'available_account': fields.many2one('account.account', 'Available account'),
        'reserved_account': fields.many2one('account.account', 'Reserved account'),
        'expense_account': fields.many2one('account.account', 'Expense account'),
        'income_account': fields.many2one('account.account', 'Income account'),
    }

class res_partner_marketplace_balance(osv.osv_memory):

    _name = "res.partner.centralbank.balance"
    _description = "Balance"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True),
        'currency_id': fields.many2one('res.currency', 'Currency', domain=[('centralbank_currency', '=', True)], required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute= dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute= dp.get_precision('Product Price')),
        'available': fields.float('Available', digits_compute= dp.get_precision('Product Price')),
        'reserved': fields.float('Reserved', digits_compute= dp.get_precision('Product Price'))
    }


class res_currency(osv.osv):

    _inherit = 'res.currency'

    _columns = {
        'centralbank_currency': fields.boolean('CentralBank currency?', readonly=True)
    }

class ir_attachment(osv.osv):

    _inherit = 'ir.attachment'

    _columns = {
        'binary_field': fields.char('Binary field', size=128)
    }

