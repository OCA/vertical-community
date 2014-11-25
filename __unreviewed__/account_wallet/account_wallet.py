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

_logger = logging.getLogger(__name__)


class AccountWalletCurrencyLine(osv.osv):

    """
    Object which contain the values of the transaction.
    Theses object can be linked to other object than account.wallet.transaction
    """

    _name = 'account.wallet.currency.line'
    _description = 'Currency line'

    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        #Compute the total value which will be transfer for the specified currency
        res = {}
        for currency in self.browse(cr, uid, ids, context=context):
            model_obj = self.pool.get(currency.model)
            res[currency.id] = 1.0
            if model_obj.search(cr, uid, [('id', '=', currency.res_id)], context=context):
                transaction = model_obj.browse(cr, uid, currency.res_id, context=context)
                res[currency.id] = transaction.quantity * currency.price_unit
        return res

    _columns = {
        'model': fields.char('Related Document Model', size=128, required=True, select=1),
        'res_id': fields.integer('Related Document ID', required=True, select=1),
        'field': fields.char('Field', size=64, required=True, select=1),
        'price_unit': fields.float('Unit price', required=True, digits_compute=dp.get_precision('Product Price')),
        'currency_id': fields.many2one('res.currency', 'Currency', domain=[('wallet_currency', '=', True)],
                                       required=True, select=1),
        'subtotal': fields.function(_get_subtotal, string='Subtotal', digits_compute=dp.get_precision('Account')),
    }

    _defaults = {
        'field': 'currency_ids'
    }

    _sql_constraints = [
        ('object_currency', 'unique(model,res_id,field,currency_id)', 'We can only have one currency per record')
    ]


class AccountWalletTransaction(osv.osv):

    """
    Main object used for transferring currencies, from sender_id to receiver_id.
    It has his own workflow, from draft to done and can be refund.
    The confirm state, used only when there is an external currency (currency whose wallet isn't managed in odoo),
     is used so the receiver can confirm that the send gave his the money.
    """

    def _get_price_char(self, cr, uid, ids, prop, unknow_none, context=None):
        # Compute a char from the currency lines, so we can easily display the transaction value in tree view
        res = {}
        for transaction in self.browse(cr, uid, ids, context=context):
            res[transaction.id] = ''
            for currency in transaction.currency_ids:
                if res[transaction.id] != '':
                    res[transaction.id] += ', '
                res[transaction.id] += str(currency.subtotal) + ' ' + currency.currency_id.symbol
        return res

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        # Control the access rights of the current user
        user_obj = self.pool.get('res.users')
        res = {}
        partner_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).partner_id.id
        for transaction in self.browse(cr, uid, ids, context=context):
            res[transaction.id] = {}
            res[transaction.id]['is_sender'] = False
            res[transaction.id]['is_receiver'] = False
            res[transaction.id]['is_moderator'] = False
            if transaction.sender_id.id == partner_id:
                res[transaction.id]['is_sender'] = True
            if transaction.receiver_id.id == partner_id:
                res[transaction.id]['is_receiver'] = True
            if user_obj.has_group(cr, uid, 'account_wallet.group_account_wallet_moderator'):
                res[transaction.id]['is_sender'] = True
                res[transaction.id]['is_receiver'] = True
                res[transaction.id]['is_moderator'] = True
        return res

    _name = 'account.wallet.transaction'
    _description = 'Transaction'
    _inherit = ['mail.thread']
    _columns = {
        'sender_id': fields.many2one('res.partner', 'Sender', required=True, readonly=True,
                                     states={'draft': [('readonly', False)]}, select=1),
        'receiver_id': fields.many2one('res.partner', 'Receiver', required=True, readonly=True,
                                       states={'draft': [('readonly', False)]}, select=1),
        'description': fields.text('Detail'),
        'total': fields.function(_get_price_char, string='Total', type="char", size=64,
                                 digits_compute=dp.get_precision('Account'), store=True, readonly=True),
        'quantity': fields.float('Exchanged quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
        'currency_ids': fields.one2many(
            'account.wallet.currency.line', 'res_id',
            domain=lambda self: [('model', '=', self._name), ('field', '=', 'currency_ids')],
            auto_join=True, string='Currencies'
        ),
        'already_published': fields.boolean('Already published?'),
        'move_ids': fields.one2many('account.move', 'wallet_transaction_id', 'Moves'),
        'reservation_id': fields.many2one('account.move', 'Reservation move'),
        'invoice_id': fields.many2one('account.move', 'Invoice move'),
        'payment_id': fields.many2one('account.move', 'Payment move'),
        'confirm_id': fields.many2one('account.move', 'Confirmation move'),
        'model_id': fields.many2one('ir.model', 'Model', required=True),
        'model_name': fields.related('model_id', 'model', type='char', size=64, string='Model', readonly=True),
        'is_sender': fields.function(_get_user_role, type="boolean", string="Is sender?", multi='role'),
        'is_receiver': fields.function(_get_user_role, type="boolean", string="Is receiver?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('confirm', 'Confirm'),
            ('done', 'Closed'),
            ('confirm_refund', 'Confirm Refund'),
            ('cancel', 'Cancelled'),
        ], 'Status', readonly=True, required=True),

    }

    def _default_partner(self, cr, uid, context=None):
        # By default, use the partner linked to the current user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.partner_id.id

    def _default_currency_ids(self, cr, uid, context=None):
        # When create the transaction, it already contain one line with the default currency
        proxy = self.pool.get('ir.model.data')
        config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
        return [(0, 0, {
            'model': self._name,
            'price_unit': 1.0,
            'currency_id': config.default_currency_id.id
        })]

    def _get_uom_id(self, cr, uid, *args):
        # Return the uom_id by default
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def _default_model(self, cr, uid, context=None):
        # Return the model by default, which is account.wallet.transaction. Otherwise, the workflow will be disabled
        proxy = self.pool.get('ir.model.data')
        result = proxy.get_object_reference(cr, uid, 'account_wallet', 'model_account_wallet_transaction')
        return result[1]

    _defaults = {
        'sender_id': _default_partner,
        'quantity': 1.0,
        'uom_id': _get_uom_id,
        'currency_ids': _default_currency_ids,
        'model_id': _default_model,
        'state': 'draft',
    }
    _order = "create_date desc"

    def _check_same_partner(self, cr, uid, ids, context=None):
        # Check if the sender and the receiver are same
        for t in self.browse(cr, uid, ids, context=context):
            if t.sender_id.id == t.receiver_id.id:
                return False
        return True

    _constraints = [
        (_check_same_partner, 'You cannot make a transaction between the same partner.', ['sender_id']),
    ]

    def unlink(self, cr, uid, ids, context=None):
        # When we remove the transaction, we also remove all linked lines
        currency_line_obj = self.pool.get('account.wallet.currency.line')
        for transaction in self.browse(cr, uid, ids, context=context):
            currency_line_ids = [c.id for c in transaction.currency_ids]
            currency_line_obj.unlink(cr, uid, currency_line_ids, context=context)
        return super(AccountWalletTransaction, self).unlink(cr, uid, ids, context=context)

    def test_access_role(self, cr, uid, ids, role_to_test, *args):
        # Raise an exception if we try to make an action denied for the current user
        res = self._get_user_role(cr, uid, ids, {}, {})
        for transaction in self.browse(cr, uid, ids):
            role = res[transaction.id]
            if not role[role_to_test]:
                raise osv.except_osv(_('Access error!'),
                                     _("You need to have the role " + role_to_test + " to perform this action!"))
        return True

    def reconcile(self, cr, uid, move_ids, context=None):
        # Reconcile all lines with same account and partner in specified moves
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
            for partner_id, res_partner in res_account.iteritems():
                if res_partner['total_debit'] == res_partner['total_credit'] and account.reconcile:
                    move_line_obj.reconcile(cr, SUPERUSER_ID, res_partner['line_ids'], context=context)

    def refund(self, cr, uid, ids, fields, context=None):
        # Reverse all moves linked to the transaction
        move_obj = self.pool.get('account.move')
        date = datetime.now().strftime("%Y-%m-%d")
        for transaction in self.browse(cr, uid, ids, context=context):

            for move_field in fields:
                move = getattr(transaction, move_field + '_id')
                if move:
                    flag = 'cancel_' + move_field
                    reversal_move_id = move_obj.create_reversals(cr, uid, [move.id], date)[0]
                    move_obj.post(cr, uid, [reversal_move_id])
                    move_obj.write(cr, uid, [reversal_move_id], {
                        'wallet_action': flag,
                        'wallet_transaction_id': transaction.id
                    }, context=context)
                    self.write(cr, uid, [transaction.id], {move_field + '_id': False}, context=context)
                    self.reconcile(cr, uid, [move.id, reversal_move_id], context=context)

    def control_amount(self, cr, uid, transaction, sender, receiver, inv=False, context=None):
        # Raise error if the balance after transaction isn't within limits
        partner_obj = self.pool.get('res.partner')

        if inv:
            temp_sender = sender
            sender = receiver
            receiver = temp_sender

        balance = partner_obj.get_wallet_balance(cr, uid, [sender.id])[sender.id]
        for currency in transaction.currency_ids:
            balance_currency = balance[currency.currency_id.id]
            if balance_currency['limit_negative'] and (balance_currency['available'] - currency.subtotal) \
                    < balance_currency['limit_negative_value']:
                raise osv.except_osv(
                    _('Limit error!'),
                    _("Not enough amount available for %s. Currency : %s, Current : %s, Needed : %s, Limit : %s")
                    % (sender.name, currency.currency_id.symbol, balance_currency['available'],
                        currency.subtotal, balance_currency['limit_negative_value'])
                )

        balance = partner_obj.get_wallet_balance(cr, uid, [receiver.id])[receiver.id]
        for currency in transaction.currency_ids:
            balance_currency = balance[currency.currency_id.id]
            if balance_currency['limit_positive'] and (balance_currency['available'] - currency.subtotal) \
                    > balance_currency['limit_positive_value']:
                raise osv.except_osv(
                    _('Limit error!'),
                    _("Too much amount available for %s. Currency : %s, Current %s, Needed : %s, Limit : %s")
                    % (receiver.name, currency.currency_id.symbol, balance_currency['available'],
                        currency.subtotal, balance_currency['limit_positive_value'])
                )

    def get_account_line(self, cr, uid, transaction, action, deduction=0.0, inv=False, name='Transaction',
                         context=None):
        # Main function which generate the accounting entries

        if not inv:
            partner_credit = transaction.sender_id
            partner_debit = transaction.receiver_id
        else:
            partner_credit = transaction.receiver_id
            partner_debit = transaction.sender_id

        if action == 'reservation':
            self.control_amount(cr, uid, transaction, transaction.sender_id, transaction.receiver_id, inv=inv,
                                context=context)
            partner_debit = partner_credit
        if action == 'confirm':
            temp_partner_debit = partner_debit
            partner_debit = partner_credit
            partner_credit = temp_partner_debit

        partner_currency_obj = self.pool.get('res.partner.wallet.currency')
        config_currency_obj = self.pool.get('account.wallet.config.currency')

        lines = []
        for currency in transaction.currency_ids:
            diff_currency_p = currency.currency_id.id != context['company_currency']
            config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id', '=', currency.currency_id.id)],
                                                             context=context)
            if not config_currency_ids:
                raise osv.except_osv(_('Config error!'), _("One of the currency is missing in the configuration!"))
            config_currency = config_currency_obj.browse(cr, uid, config_currency_ids, context=context)[0]
            debit_availability_account = config_currency.partner_availability_account_id.id
            debit_reserved_account = config_currency.partner_reserved_account_id.id
            debit_expense_account = config_currency.partner_expense_account_id.id
            credit_availability_account = config_currency.partner_availability_account_id.id
            credit_reserved_account = config_currency.partner_reserved_account_id.id
            credit_income_account = config_currency.partner_income_account_id.id

            if action == 'confirm' and not config_currency.external_currency:
                continue

            partner_currency_ids = partner_currency_obj.search(
                cr, uid,
                [('partner_id', '=', partner_debit.id), ('currency_id', '=', currency.currency_id.id)],
                context=context
            )
            for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
                if 'availability_account' in partner_currency and partner_currency.availability_account:
                    debit_availability_account = partner_currency.availability_account.id
                if 'reserved_account' in partner_currency and partner_currency.reserved_account:
                    debit_reserved_account = partner_currency.reserved_account.id
                if 'expense_account' in partner_currency and partner_currency.expense_account:
                    debit_expense_account = partner_currency.expense_account.id

            partner_currency_ids = partner_currency_obj.search(
                cr, uid,
                [('partner_id', '=', partner_credit.id), ('currency_id', '=', currency.currency_id.id)],
                context=context
            )
            for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
                if 'availability_account' in partner_currency and partner_currency.availability_account:
                    credit_availability_account = partner_currency.availability_account.id
                if 'reserved_account' in partner_currency and partner_currency.reserved_account:
                    credit_reserved_account = partner_currency.reserved_account.id
                if 'income_account' in partner_currency and partner_currency.income_account:
                    credit_income_account = partner_currency.income_account.id

            currency_id = currency.currency_id.id
            price = currency.subtotal - deduction
            account_debit_id = False
            account_credit_id = False
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

            lines.append((0, 0, {
                'name': name,
                'partner_id': partner_debit and partner_debit.id or False,
                'account_id': account_debit_id,
                'debit': price,
                'amount_currency': diff_currency_p and price or False,
                'currency_id': diff_currency_p and currency_id or False,
                'quantity': transaction.quantity,
                'product_uom_id': transaction.uom_id.id,
            }))
            lines.append((0, 0, {
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
        # Generate the specified accounting move
        partner_obj = self.pool.get('res.partner')
        move_obj = self.pool.get('account.move')
        company_obj = self.pool.get('res.company')
        config = self.pool.get('ir.model.data').get_object(cr, uid, 'base_community', 'community_settings')

        date = datetime.now().date().strftime("%Y-%m-%d")

        context = {}
        company_id = company_obj._company_default_get(cr, uid)
        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id
        for transaction in self.browse(cr, uid, ids, context=context):

            lines = self.get_account_line(cr, uid, transaction, action, context=context)

            if lines:
                ref = 'Transaction'
                journal_id = config.journal_id.id
                move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
                move['wallet_transaction_id'] = transaction.id
                move['wallet_action'] = action
                move_id = move_obj.create(cr, uid, move)
                move_obj.write(cr, uid, [move_id], {'line_id': lines})
                move_obj.post(cr, uid, [move_id])
                self.write(cr, uid, [transaction.id], {action + '_id': move_id})
                if transaction.reservation_id:
                    self.reconcile(cr, uid, [transaction.reservation_id.id, move_id], context=context)

            partner_obj.update_wallet_balance(
                cr, uid,
                [transaction.sender_id.id, transaction.receiver_id.id],
                context=context
            )

    def get_skip_confirm(self, cr, uid, transaction, context=None):
        # Check is there is an external currency, to determine whether we should go to confirm or paid state
        config_currency_obj = self.pool.get('account.wallet.config.currency')

        currency_ids = []
        for currency in transaction.currency_ids:
            currency_ids.append(currency.currency_id.id)
        config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id', 'in', currency_ids)])

        skip_confirm = True
        for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids):
            if config_currency.external_currency:
                skip_confirm = False
        return skip_confirm

    def confirm(self, cr, uid, ids, *args):
        # Workflow action which confirm the transaction and make the payment for currency managed inside Odoo,
        #  it goes to confirm or paid state whether there is or not an external currency
        self.test_access_role(cr, uid, ids, 'is_sender', *args)

        self.write(cr, uid, ids, {'already_published': True})
        for transaction in self.browse(cr, uid, ids):
            self.prepare_move(cr, uid, [transaction.id], 'reservation')
            self.prepare_move(cr, uid, [transaction.id], 'payment')

            skip_confirm = self.get_skip_confirm(cr, uid, transaction)
            if not skip_confirm:
                workflow.trg_validate(uid, 'account.wallet.transaction', transaction.id,
                                      'transaction_draft_confirm', cr)
            else:
                workflow.trg_validate(uid, 'account.wallet.transaction', transaction.id, 'transaction_draft_done', cr)
        return True

    def change_state(self, cr, uid, ids, new_state, *args):
        # Called by workflow, launch needed action depending of the next state
        for transaction in self.browse(cr, uid, ids):
            fields = {'state': new_state}
            if new_state == 'done':
                self.prepare_move(cr, uid, [transaction.id], 'confirm')
            if new_state == 'cancel':
                self.refund(cr, uid, [transaction.id], ['reservation', 'invoice', 'payment', 'confirm'])
            self.write(cr, uid, [transaction.id], fields)
        return True

    def reset_workflow(self, cr, uid, ids, *args):
        # Called by workflow, launch needed action depending of the next state and reset the workflow
        for transaction in self.browse(cr, uid, ids):
            state = transaction.state
            role_to_test = 'is_sender'
            if state == 'done':
                role_to_test = 'is_receiver'
            self.test_access_role(cr, uid, ids, role_to_test, *args)

            workflow.trg_delete(uid, 'account.wallet.transaction', transaction.id, cr)
            workflow.trg_create(uid, 'account.wallet.transaction', transaction.id, cr)

            if state == 'done':
                skip_confirm = self.get_skip_confirm(cr, uid, transaction)
                if not skip_confirm:
                    workflow.trg_validate(uid, 'account.wallet.transaction',
                                          transaction.id, 'transaction_draft_confirm_refund', cr)
                else:
                    workflow.trg_validate(uid, 'account.wallet.transaction',
                                          transaction.id, 'transaction_done_cancel_through_draft', cr)
        return True


class AccountMove(osv.osv):

    """
    Add fields to link account move to the wallet transaction
    """

    _inherit = 'account.move'

    _columns = {
        'wallet_transaction_id': fields.many2one('account.wallet.transaction', 'Transaction'),
        'wallet_action': fields.selection([
            ('reservation', 'Reservation'),
            ('invoice', 'Invoice'),
            ('payment', 'Payment'),
            ('confirm', 'Payment confirmation'),
            ('cancel_reservation', 'Reservation Cancellation'),
            ('cancel_invoice', 'Refund'),
            ('cancel_payment', 'Refund Payment'),
            ('cancel_confirm', 'Payment confirmation cancellation'),
        ], 'Type', readonly=True),
    }


class ResPartner(osv.osv):

    """
    Display balance in partner form and add element for configuration specific to the partner
    """

    _inherit = 'res.partner'

    def get_wallet_limits(self, cr, uid, ids, currency_ids, context=None):
        # Get the wallet limits for specified partners from general and partner config

        partner_currency_obj = self.pool.get('res.partner.wallet.currency')
        config_currency_obj = self.pool.get('account.wallet.config.currency')

        config_currency_ids = config_currency_obj.search(
            cr, uid,
            [('currency_id', 'in', currency_ids)],
            context=context
        )
        config_currency_limits = {}
        for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids, context=context):
            config_currency_limits[config_currency.currency_id.id] = {
                'limit_negative': config_currency.limit_negative,
                'limit_negative_value': config_currency.limit_negative_value,
                'limit_positive': config_currency.limit_positive,
                'limit_positive_value': config_currency.limit_positive_value
            }

        partner_currency_ids = partner_currency_obj.search(
            cr, uid,
            [('partner_id', 'in', ids), ('currency_id', 'in', currency_ids)],
            context=context
        )
        partner_currency_limits = {}
        for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
            if not partner_currency.partner_id.id in partner_currency_limits:
                partner_currency_limits[partner_currency.partner_id.id] = {}
            partner_currency_limits[partner_currency.partner_id.id][partner_currency.currency_id.id] = {
                'limit_negative': partner_currency.limit_negative,
                'limit_negative_value': partner_currency.limit_negative_value,
                'limit_positive': partner_currency.limit_positive,
                'limit_positive_value': partner_currency.limit_positive_value,
            }

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = {}
            for currency_id in currency_ids:
                res[partner.id][currency_id] = config_currency_limits[currency_id]
                if partner.id in partner_currency_limits and currency_id in partner_currency_limits[partner.id]:
                    res[partner.id][currency_id] = partner_currency_limits[partner.id][currency_id]

        return res

    def get_wallet_balance(self, cr, uid, ids, context=None):
        # Compute balances for specified partner
        if not context:
            context = {}
        ctx = context.copy()
        ctx['all_fiscalyear'] = True

        company_obj = self.pool.get('res.company')
        company_id = company_obj._company_default_get(cr, uid)
        company_currency_id = company_obj.browse(cr, uid, [company_id])[0].currency_id.id

        config_currency_obj = self.pool.get('account.wallet.config.currency')
        partner_currency_obj = self.pool.get('res.partner.wallet.currency')
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

        partner_currencies = {}
        partner_currency_ids = partner_currency_obj.search(
            cr, uid,
            [('partner_id', 'in', ids), ('currency_id', 'in', currency_ids)],
            context=context
        )
        for partner_currency in partner_currency_obj.browse(cr, uid, partner_currency_ids, context=context):
            if not partner_currency.currency_id.id in partner_currencies:
                partner_currencies[partner_currency.currency_id.id] = {}
            accounts = {
                'available': False
            }
            if partner_currency.available_account:
                account_id = partner_currency.available_account.id
                account_ids[account_id] = account_id
                accounts['available'] = account_id
            accounts['reserved'] = False
            if partner_currency.reserved_account:
                account_id = partner_currency.reserved_account.id
                account_ids[account_id] = account_id
                accounts['reserved'] = account_id
            partner_currencies[partner_currency.currency_id.id][partner_currency.partner_id.id] = accounts

        query = self.pool.get('account.move.line')._query_get(cr, uid, context=ctx)

        cr.execute("""SELECT l.partner_id, SUM(l.debit-l.credit), l.account_id, l.currency_id, a.code
                      FROM account_move_line l
                      LEFT JOIN account_account a ON (l.account_id=a.id)
                      WHERE l.partner_id IN %s
                      AND a.id IN %s
                      AND l.reconcile_id IS NULL
                      AND """ + query + """
                      GROUP BY l.partner_id, l.account_id, l.currency_id, a.code
                      """,
                   (tuple(ids), tuple(account_ids)))
        res = {}
        for pid, val, account_id, currency_id, code in cr.fetchall():
            if not currency_id:
                currency_id = company_currency_id
            if val is None:
                val = 0
            if not currency_id in res:
                res[currency_id] = {}
            if not pid in res[currency_id]:
                res[currency_id][pid] = {}
            res[currency_id][pid][account_id] = val

        res_final = {}
        partners = self.browse(cr, uid, ids, context=context)

        limits = self.get_wallet_limits(cr, uid, ids, currency_ids, context=context)

        for partner in partners:
            pid = partner.id
            res_final[pid] = {}

            for currency_id in currency_ids:
                vals = {
                    'partner_id': partner.id, 'currency_id': currency_id,
                    'limit_negative': limits[partner.id][currency_id]['limit_negative'],
                    'limit_negative_value': limits[partner.id][currency_id]['limit_negative_value'],
                    'limit_positive': limits[partner.id][currency_id]['limit_positive'],
                    'limit_positive_value': limits[partner.id][currency_id]['limit_positive_value']
                }

                if currency_id in partner_currencies and pid in partner_currencies[currency_id] \
                        and 'available' in partner_currencies[currency_id][pid] \
                        and partner_currencies[currency_id][pid]['available']:
                    account_id = partner_currencies[currency_id][pid]['available']
                else:
                    account_id = default_account[currency_id]['available']

                vals['available'] = \
                    currency_id in res and pid in res[currency_id] \
                    and account_id in res[currency_id][pid] and res[currency_id][pid][account_id] or 0.0
                if currency_id in partner_currencies and pid in partner_currencies[currency_id] \
                        and 'reserved' in partner_currencies[currency_id][pid] \
                        and partner_currencies[currency_id][pid]['reserved']:
                    account_id = partner_currencies[currency_id][pid]['reserved']
                else:
                    account_id = default_account[currency_id]['reserved']
                vals['reserved'] = \
                    currency_id in res and pid in res[currency_id] \
                    and account_id in res[currency_id][pid] \
                    and res[currency_id][pid][account_id] or 0.0
                res_final[pid][currency_id] = vals

        return res_final

    def update_wallet_balance(self, cr, uid, ids, context=None):
        # Update the balance on specified partner
        line_obj = self.pool.get('res.partner.wallet.balance')
        balances = self.get_wallet_balance(cr, uid, ids, context=context)

        lines = {}
        line_ids = line_obj.search(cr, uid, [('partner_id', 'in', ids)], context=context)
        for line in line_obj.browse(cr, uid, line_ids, context=context):
            if line.partner_id.id not in lines:
                lines[line.partner_id.id] = {}
            lines[line.partner_id.id][line.currency_id.id] = line.id

        res = {}
        for partner in self.browse(cr, uid, ids, context=context):
            res[partner.id] = []
            for currency in balances[partner.id].values():
                if partner.id in lines and currency['currency_id'] in lines[partner.id]:
                    line_id = lines[partner.id][currency['currency_id']]
                    del currency['partner_id']
                    del currency['currency_id']
                    line_obj.write(cr, uid, [line_id], currency, context=context)
                else:
                    line_obj.create(cr, uid, currency, context=context)

        return res

    def create(self, cr, uid, vals, context=None):
        # Trigger an update balance at creation
        res = super(ResPartner, self).create(cr, uid, vals, context=context)
        self.update_wallet_balance(cr, uid, [res], context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # Trigger an update balance when we make change in currency configuration in partner
        res = super(ResPartner, self).write(cr, uid, ids, vals, context=context)
        if 'wallet_currency_ids' in vals:
            self.update_wallet_balance(cr, uid, ids, context=context)
        return res

    _columns = {
        'wallet_currency_ids': fields.one2many('res.partner.wallet.currency', 'partner_id', 'Currencies'),
        'wallet_balance_ids': fields.one2many("res.partner.wallet.balance", 'partner_id', 'Balances', readonly=True),
        'create_date': fields.datetime('Create date'),
    }


class ResPartnerWalletCurrency(osv.osv):

    """
    Lines for configuring wallet for each currency in partner
    """

    _name = "res.partner.wallet.currency"
    _description = "Currency"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
        'currency_id': fields.many2one('res.currency', 'Currency',
                                       domain=[('wallet_currency', '=', True)], required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute=dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute=dp.get_precision('Product Price')),
        'available_account': fields.many2one('account.account', 'Available account'),
        'reserved_account': fields.many2one('account.account', 'Reserved account'),
        'expense_account': fields.many2one('account.account', 'Expense account'),
        'income_account': fields.many2one('account.account', 'Income account'),
    }


class ResPartnerWalletBalance(osv.osv):

    """
    Lines for displaying balances in partner
    """

    _name = "res.partner.wallet.balance"
    _description = "Balance"

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', required=True, ondelete='cascade'),
        'currency_id': fields.many2one('res.currency', 'Currency',
                                       domain=[('wallet_currency', '=', True)], required=True),
        'limit_negative': fields.boolean('Limit - ?'),
        'limit_negative_value': fields.float('ValueLimit -', digits_compute=dp.get_precision('Product Price')),
        'limit_positive': fields.boolean('Limit + ?'),
        'limit_positive_value': fields.float('Value Limit +', digits_compute=dp.get_precision('Product Price')),
        'available': fields.float('Available', digits_compute=dp.get_precision('Product Price')),
        'reserved': fields.float('Reserved', digits_compute=dp.get_precision('Product Price'))
    }

    #TODO
    # I can't activate this constraint because it cause bugs with tests
    # _sql_constraints = [
    #    ('balance', 'unique(partner_id,currency_id)',
    #     'There was an error when computing the partner balance, tried to create a line while another already exist')
    # ]


class ResCurrency(osv.osv):

    """
    Add a boolean in currency to identify currency usable in wallet
    """
    _inherit = 'res.currency'

    _columns = {
        'wallet_currency': fields.boolean('Wallet currency?', readonly=True)
    }
