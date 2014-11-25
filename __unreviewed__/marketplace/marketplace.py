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
import openerp.addons.decimal_precision as dp

from openerp.osv import fields, osv, orm
from openerp import SUPERUSER_ID
from openerp import workflow
from openerp.tools.translate import _
from datetime import datetime

_logger = logging.getLogger(__name__)


class MarketplaceAnnouncementCategory(osv.osv):

    """
    Announcement category, we can only have one category per announcement. Recursive.
    """

    _name = 'marketplace.announcement.category'
    _description = 'Offers/Wants Categories'
    _inherit = ['vote.category', 'base.recursive.model']
    _columns = {
        'name': fields.char('Category Name', required=True, size=64, translate=True),
        'parent_id': fields.many2one('marketplace.announcement.category', 'Parent', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('marketplace.announcement.category', 'parent_id', 'Childs'),
        'sequence': fields.integer('Sequence'),
        'tag_ids': fields.one2many('marketplace.tag', 'category_id', 'Tags'),
        'active': fields.boolean(
            'Active', help="The active field allows you to hide the category without removing it."
        ),
        'partner_ids': fields.many2many(
            'res.partner', 'res_partner_marketplace_category_rel', 'category_id', 'partner_id', 'Partners'
        ),
    }
    _defaults = {
        'active': 1,
    }


class MarketplaceTag(osv.osv):

    """
    Announcement tag, you can assigned several tag per announcement. Tag are linked to the category specified in
     the announcement.
    """

    _name = 'marketplace.tag'
    _description = 'Tag'
    _columns = {
        'name': fields.char('Tag', required=True, size=64, translate=True),
        'category_id': fields.many2one(
            'marketplace.announcement.category', 'Category', ondelete='cascade', required=True
        ),
        'partner_ids': fields.many2many(
            'res.partner', 'res_partner_marketplace_tag_rel', 'tag_id', 'partner_id', 'Partners'
        ),
    }
    _order = 'category_id, name'


class MarketplaceAnnouncement(osv.osv):

    """
    Object containing the announcement from the users. Can be either an offer or a demand
    """

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        # Control the access rights of the current user
        res = {}
        partner_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).partner_id.id
        for transaction in self.browse(cr, uid, ids, context=context):
            res[transaction.id] = {}
            res[transaction.id]['is_user'] = False
            res[transaction.id]['is_moderator'] = False
            if transaction.partner_id.id == partner_id:
                res[transaction.id]['is_user'] = True
            if self.pool.get('res.users').has_group(cr, uid, 'account_wallet.group_account_wallet_moderator'):
                res[transaction.id]['is_user'] = True
                res[transaction.id]['is_moderator'] = True
        return res

    def _get_address(self, cr, uid, ids, prop, unknow_none, context=None):
        # Compute the full adress to display it in only one text field
        res = {}
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = announcement.street or ''
            res[announcement.id] += ' ' + (announcement.street2 or '')
            res[announcement.id] += ', ' + (announcement.zip or '')
            res[announcement.id] += ' ' + (announcement.city or '')
            res[announcement.id] += ', ' + (announcement.state_id and announcement.state_id.name or '')
            res[announcement.id] += ' ' + (announcement.country_id and announcement.country_id.name or '')
        return res

    def _get_qty_available(self, cr, uid, ids, prop, unknow_none, context=None):
        # Compute the quantity available in the announcement
        proposition_obj = self.pool.get('marketplace.proposition')
        res = {}
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = announcement.quantity
            proposition_ids = proposition_obj.search(
                cr, uid, [
                    ('announcement_id', '=', announcement.id),
                    ('state', 'in', ['accepted', 'invoiced', 'confirm', 'paid', 'confirm_refund'])
                ], context=context
            )
            for proposition in proposition_obj.browse(cr, uid, proposition_ids, context=context):
                res[announcement.id] -= proposition.quantity
            if res[announcement.id] < 0 or announcement.infinite_qty:
                res[announcement.id] = 0
        return res

    def _get_binary_filesystem(self, cr, uid, ids, name, arg, context=None):
        # Get picture from ir.attachment
        res = {}
        attachment_obj = self.pool.get('ir.attachment')

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = False
            attachment_ids = attachment_obj.search(
                cr, uid,
                [('res_model', '=', self._name), ('res_id', '=', record.id), ('binary_field', '=', name)],
                context=context
            )
            if attachment_ids:
                img = attachment_obj.browse(cr, uid, attachment_ids, context=context)[0].datas
                res[record.id] = img
        return res

    def _set_binary_filesystem(self, cr, uid, id, name, value, arg, context=None):
        # Set picture in ir.attachment
        attachment_obj = self.pool.get('ir.attachment')

        attachment_ids = attachment_obj.search(
            cr, uid, [('res_model', '=', self._name), ('res_id', '=', id), ('binary_field', '=', name)], context=context
        )
        if value:
            if attachment_ids:
                attachment_obj.write(cr, uid, attachment_ids, {'datas': value}, context=context)
            else:
                attachment_obj.create(
                    cr, uid, {
                        'res_model': self._name, 'res_id': id, 'name': 'Marketplace picture',
                        'binary_field': name, 'datas': value, 'datas_fname': 'picture.jpg'
                    }, context=context
                )
        else:
            attachment_obj.unlink(cr, uid, attachment_ids, context=context)

    _name = "marketplace.announcement"
    _description = 'Offer/Want'
    _inherit = ['mail.thread', 'vote.model']
    _inherits = {'vote.evaluated': "vote_evaluated_id"}
    _columns = {
        'name': fields.char('What', size=64, required=True),
        'type': fields.selection([
            ('offer', 'I offer'),
            ('want', 'I want'),
        ], 'Type', required=True),
        'description': fields.text('Description'),
        'picture': fields.function(
            _get_binary_filesystem, fnct_inv=_set_binary_filesystem, type='binary', string='Picture'
        ),
        'expiration_date': fields.date('Expiry on'),
        'category_id': fields.many2one('marketplace.announcement.category', 'Category'),
        'tag_ids': fields.many2many(
            'marketplace.tag', 'marketplace_announcement_tag_rel', 'announcement_id', 'tag_id', 'Tags'
        ),
        'partner_id': fields.many2one('res.partner', 'Who', required=True, readonly=True),
        'infinite_qty': fields.boolean('Unlimited'),
        'quantity': fields.float('Quantity', digits_compute=dp.get_precision('Product Unit of Measure')),
        'quantity_available': fields.function(
            _get_qty_available, type="float", string="Available",
            digits_compute=dp.get_precision('Product Unit of Measure'), readonly=True
        ),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
        'currency_mode': fields.selection(
            [('one', 'I propose one of the following currencies'), ('all', 'I propose all the following currencies')],
            'Currency mode'
        ),
        'currency_ids': fields.one2many(
            'account.wallet.currency.line', 'res_id',
            domain=lambda self: [('model', '=', self._name), ('field', '=', 'currency_ids')],
            auto_join=True, string='Currencies'
        ),
        'date_from': fields.date('From'),
        'date_to': fields.date('To'),
        'create_date': fields.datetime('Create date'),
        'publish_date': fields.datetime('Published on'),
        'proposition_ids': fields.one2many('marketplace.proposition', 'announcement_id', 'Propositions'),
        'address': fields.function(_get_address, type="char", size=512, string="Where", store=True, readonly=True),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'State'),
        'country_id': fields.many2one('res.country', 'Country'),
        'is_user': fields.function(_get_user_role, type="boolean", string="Is user?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'vote_evaluated_id': fields.many2one('vote.evaluated', 'Evaluated', ondelete="cascade", required=True),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('open', 'Published'),
            ('done', 'Closed'),
            ('cancel', 'Cancelled'),
        ], 'Status', readonly=True, required=True),
    }

    def _get_uom_id(self, cr, uid, *args):
        # Get default uom
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def _default_currency_ids(self, cr, uid, context=None):
        # When create the announcement, it already contain one line with the default currency
        proxy = self.pool.get('ir.model.data')
        config = proxy.get_object(cr, uid, 'base_community', 'community_settings')
        return [(0, 0, {
            'model': self._name,
            'price_unit': 1.0,
            'currency_id': config.default_currency_id.id,
            'field': 'currency_ids'
        })]

    def _default_partner(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return user.partner_id.id

    def _default_street(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['street']

    def _default_street2(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['street2']

    def _default_zip(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['zip']

    def _default_city(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['city']

    def _default_state_id(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['state_id']

    def _default_country_id(self, cr, uid, context=None):
        # Get the partner linked to the user
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)
        return self.onchange_author(cr, uid, [], user.partner_id.id, context=context)['value']['country_id']

    _defaults = {
        'type': 'offer',
        'currency_mode': 'one',
        'partner_id': _default_partner,
        'street': _default_street,
        'street2': _default_street2,
        'zip': _default_zip,
        'city': _default_city,
        'state_id': _default_state_id,
        'country_id': _default_country_id,
        'currency_ids': _default_currency_ids,
        'quantity': 1.0,
        'uom_id': _get_uom_id,
        'state': 'draft',
    }
    _order = "create_date desc"

    def test_close(self, cr, uid, ids, context=None):
        # Auto close the announcement when all available are sold
        for announcement in self.browse(cr, uid, ids, context=context):
            if announcement.state == 'open' and announcement.quantity_available == 0 and not announcement.infinite_qty:
                workflow.trg_validate(
                    SUPERUSER_ID, 'marketplace.announcement', announcement.id, 'announcement_open_done', cr
                )

    def onchange_author(self, cr, uid, ids, partner_id, context=None):
        # Update the address when we change the author
        partner_obj = self.pool.get('res.partner')
        partner = partner_obj.browse(cr, uid, partner_id, context=context)
        res = {
            'street': partner.street,
            'street2': partner.street2,
            'zip': partner.zip,
            'city': partner.city,
            'state_id': partner.state_id.id,
            'country_id': partner.country_id.id,
        }
        return {
            'value': res
        }

    def test_access_role(self, cr, uid, ids, role_to_test, *args):
        # Raise an exception if we try to make an action denied for the current user
        res = self._get_user_role(cr, uid, ids, {}, {})
        for announcement in self.browse(cr, uid, ids):
            role = res[announcement.id]
            if not role[role_to_test]:
                raise osv.except_osv(
                    _('Access error!'),
                    _("You need to have the role " + role_to_test + " to perform this action!")
                )
        return True

    def change_state(self, cr, uid, ids, new_state, *args):
        # Called by workflow, launch needed action depending of the next state
        for announcement in self.browse(cr, uid, ids):
            #_logger.info('uid %s, new_state %s', uid, new_state)
            fields = {'state': new_state}
            self.write(cr, uid, [announcement.id], fields)

    def publish(self, cr, uid, ids, *args):
        # Publish the announcement
        for announcement in self.browse(cr, uid, ids):
            fields = {'state': 'open'}
            if not announcement.publish_date:
                fields['publish_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.write(cr, uid, [announcement.id], fields)

    def reset_workflow(self, cr, uid, ids, *args):
        # Called by workflow, launch needed action depending of the next state and reset the workflow
        self.test_access_role(cr, uid, ids, 'is_user', *args)
        for announcement in self.browse(cr, uid, ids):
            state = announcement.state
            self.write(cr, uid, [announcement.id], {'state': 'draft'})
            workflow.trg_delete(uid, 'marketplace.announcement', announcement.id, cr)
            workflow.trg_create(uid, 'marketplace.announcement', announcement.id, cr)
            if state == 'done':
                workflow.trg_validate(uid, 'marketplace.announcement', announcement.id, 'announcement_draft_open', cr)
        return True

    def add_proposition(self, cr, uid, ids, context):
        # When button pressed, open a popup to create a new proposition
        announcement = self.browse(cr, uid, ids, context=context)[0]

        return {
            'type': 'ir.actions.act_window',
            'name': 'Model Title', 
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'marketplace.proposition',
            'target': 'new',
            'context': {
                'default_announcement_id': ids[0],
                'default_uom_id': announcement.uom_id.id
            }
        }


class MarketplaceProposition(osv.osv):

    """
    Object containing the proposition to the announcement. Inherit transaction and so update balances when closed.
    """

    def _get_vote_voters(self, cr, uid, ids, name, args, context=None):
        # Get the list of partner which must vote in order to close the proposition
        res = {}
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = [(6, 0, [record.sender_id.id, record.receiver_id.id])]
        return res

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        # Control the access rights of the current user
        transaction_ids = []
        for proposition in self.browse(cr, uid, ids, context=context):
            transaction_ids.append(proposition.transaction_id.id)

        res = self.pool.get('account.wallet.transaction')._get_user_role(
            cr, uid, transaction_ids, prop, unknow_none, context=context
        )
        for proposition in self.browse(cr, uid, ids, context=context):
            values = res[proposition.transaction_id.id]
            values['is_user'] = False
            values['is_announcer'] = False
            values['is_dispute'] = False
            values['is_moderator_or_aggree'] = False

            if proposition.type == 'want':
                is_sender = False
                if values['is_sender']:
                    is_sender = True
                values['is_sender'] = False
                if values['is_receiver']:
                    values['is_sender'] = True
                values['is_receiver'] = False
                if is_sender:
                    values['is_receiver'] = True

            if values['is_sender']:
                values['is_dispute'] = True
                if proposition.type == 'offer':
                    values['is_user'] = True
                else:
                    values['is_announcer'] = True

            if values['is_receiver']:
                values['is_dispute'] = True
                if proposition.type == 'offer':
                    values['is_announcer'] = True
                else:
                    values['is_user'] = True

            if (values['is_dispute'] and proposition.want_cancel_user
                    and proposition.want_cancel_announcer) or values['is_moderator']:
                values['is_moderator_or_aggree'] = True

            res[proposition.id] = values
        return res

    _name = 'marketplace.proposition'
    _description = 'Proposition'
    _inherits = {'account.wallet.transaction': "transaction_id"}
    _inherit = ['mail.thread', 'vote.model']
    _vote_category_field = 'category_id'
    _vote_category_model = 'marketplace.announcement.category'
    _columns = {
        'transaction_id': fields.many2one(
            'account.wallet.transaction', 'Transaction', ondelete="cascade", required=True, auto_join=True
        ),
        'announcement_id': fields.many2one('marketplace.announcement', 'What', required=True),
        'name': fields.related('announcement_id', 'name', type='char', string='Name', store=True),
        'type': fields.related('announcement_id', 'type', type='char', string='Type', store=True),
        'city': fields.related(
            'announcement_id', 'city',
            type='char', size=128, string='City', store=True
        ),
        'country_id': fields.related(
            'announcement_id', 'country_id', type='many2one',
            relation='res.country', string='Country', store=True
        ),
        'description_announcement_id': fields.many2one('marketplace.announcement', 'Link to announcement description'),
        'category_id': fields.related(
            'announcement_id', 'category_id', type="many2one", store=True,
            relation="marketplace.announcement.category", string='Category'
        ),
        'want_cancel_user': fields.boolean('(Replyer) Cancel the transaction'),
        'want_cancel_announcer': fields.boolean('(Announcer) Cancel the transaction'),
        'call_moderator_user': fields.boolean('(Replyer) Call moderator?'),
        'call_moderator_announcer': fields.boolean('(Announcer) Call moderator?'),
        'already_published': fields.boolean('Already published?'),
        'already_accepted': fields.boolean('Already accepted?'),
        'vote_voters': fields.function(_get_vote_voters, type='many2many', obj='res.partner', string='Voters'),
        'is_user': fields.function(_get_user_role, type="boolean", string="Is user?", multi='role'),
        'is_announcer': fields.function(_get_user_role, type="boolean", string="Is announcer?", multi='role'),
        'is_dispute': fields.function(_get_user_role, type="boolean", string="Is in dispute?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'is_moderator_or_aggree': fields.function(
            _get_user_role, type="boolean", string="Is moderator or aggreed?", multi='role'
        ),
        'skip_confirm': fields.boolean('Skip confirm'),
        'skip_vote': fields.boolean('Skip vote?'),
        'state': fields.selection([
            ('draft', 'Draft'),
            ('open', 'Open'),
            ('accepted', 'Accepted'),
            ('rejected', 'Rejected'),
            ('invoiced', 'Invoiced'),
            ('confirm', 'Payment confirmation'),
            ('vote', 'Waiting for votes'),
            ('paid', 'Paid'),
            ('confirm_refund', 'Refund payment confirmation'),
            ('cancel', 'Cancelled'),
        ], 'Status', readonly=True, required=True),
    }

    def _default_currency_ids(self, cr, uid, context=None):
        # By default, fill with the currencies of the announcement
        if context is None:
            context = {}
        currency_ids = [] 
        if context.get('default_announcement_id'):
            for currency in self.pool.get('marketplace.announcement').browse(
                    cr, uid, [context.get('default_announcement_id')], context=context
            )[0].currency_ids:
                currency_ids.append((0, 0, {
                    'model': self._name,
                    'price_unit': currency.price_unit,
                    'currency_id': currency.currency_id.id,
                    'field': 'currency_ids'
                }))
        return currency_ids

    def _default_model(self, cr, uid, context=None):
        # Fill with marketplace.proposition, to indicate that it's not a simple transaction
        proxy = self.pool.get('ir.model.data')
        result = proxy.get_object_reference(cr, uid, 'marketplace', 'model_marketplace_proposition')
        return result[1]

    _defaults = {
        'currency_ids': _default_currency_ids,
        'model_id': _default_model,
        'state': 'draft',
        'skip_vote': True
    }

#    _order = "create_date desc" TODO reference to create date ambiguous because of wallet.transaction

    def test_access_role(self, cr, uid, ids, role_to_test, *args):
        # Raise an exception if we try to make an action denied for the current user
        res = self._get_user_role(cr, uid, ids, {}, {})
        for proposition in self.browse(cr, uid, ids):
            role = res[proposition.id]
            if not role[role_to_test]:
                raise osv.except_osv(
                    _('Access error!'),
                    _("You need to have the role " + role_to_test + " to perform this action!")
                )
        return True

    def _get_evaluated(self, cr, uid, id, partner_id, context=None):
        # Return partner and announcement which are gonna be evaluated
        proposition = self.browse(cr, uid, id, context=context)
        res = []
        if proposition.sender_id.id == partner_id:
            if proposition.receiver_id.vote_evaluated_id:
                res.append(proposition.receiver_id.vote_evaluated_id.id)
            if proposition.announcement_id.vote_evaluated_id:
                res.append(proposition.announcement_id.vote_evaluated_id.id)
        else:
            if proposition.sender_id.vote_evaluated_id:
                res = [proposition.sender_id.vote_evaluated_id.id]
        return res

    def test_vote(self, cr, uid, ids, context=None):
        # Check the votes, to know if all required votes are made and if we can close the proposition
        transaction_obj = self.pool.get('account.wallet.transaction')
        vote_obj = self.pool.get('vote.vote')

        for proposition in self.browse(cr, uid, ids, context=context):
            vote_user = False
            vote_announcer = False
            user_partner_id = proposition.sender_id.id
            announcer_partner_id = proposition.receiver_id.id
            vote_ids = vote_obj.search(
                cr, uid, [
                    ('model', '=', 'marketplace.proposition'), ('res_id', '=', proposition.id),
                    ('partner_id', 'in', [user_partner_id, announcer_partner_id])
                ], context=context)
            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
                if vote.partner_id.id == user_partner_id:
                    vote_user = vote
                if vote.partner_id.id == announcer_partner_id:
                    vote_announcer = vote

            if (vote_user and vote_user.is_complete and vote_announcer and vote_announcer.is_complete)\
                    or proposition.skip_vote:
                workflow.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_vote_paid', cr)
                transaction_obj.write(cr, uid, [proposition.transaction_id.id], {'state': 'done'}, context=context)
                workflow.trg_delete(uid, 'account.wallet.transaction', proposition.transaction_id.id, cr)

    def change_state(self, cr, uid, ids, new_state, *args):
        # Called by workflow, launch needed action depending of the next state
        announcement_obj = self.pool.get('marketplace.announcement')
        transaction_obj = self.pool.get('account.wallet.transaction')
        for proposition in self.browse(cr, uid, ids):
            fields = {'state': new_state}
            if proposition.state == 'draft' and new_state == 'open':
                if proposition.quantity > \
                        proposition.announcement_id.quantity_available and not proposition.announcement_id.infinite_qty:
                    raise osv.except_osv(_('Access error!'), _("There is not enough quantity available!"))
                transaction_obj.write(cr, uid, [proposition.transaction_id.id], {'state': 'draft'})
                workflow.trg_delete(uid, 'account.wallet.transaction', proposition.transaction_id.id, cr)
                fields['already_published'] = True
            if proposition.state == 'open' and new_state == 'accepted':
                transaction_obj.prepare_move(cr, uid, [proposition.transaction_id.id], 'reservation')
                announcement_obj.test_close(cr, uid, [proposition.announcement_id.id])
                fields['already_accepted'] = True
            if proposition.state == 'accepted' and new_state == 'invoiced':
                transaction_obj.prepare_move(cr, uid, [proposition.transaction_id.id], 'invoice')
            if new_state == 'cancel':
                transaction_obj.refund(
                    cr, uid, [proposition.transaction_id.id], ['reservation', 'invoice', 'payment', 'confirm']
                )
                transaction_obj.write(cr, uid, [proposition.transaction_id.id], {'state': 'cancel'})
                workflow.trg_delete(uid, 'account.wallet.transaction', proposition.transaction_id.id, cr)

            self.write(cr, SUPERUSER_ID, [proposition.id], fields)

            if new_state == 'accepted':
                announcement_obj.test_close(cr, uid, [proposition.announcement_id.id])

    def pay(self, cr, uid, ids, *args):
        # Launch the payment of the proposition. If an external currency is needed, it go to the confirm state
        transaction_obj = self.pool.get('account.wallet.transaction')
        self.test_access_role(cr, uid, ids, 'is_sender', *args)

        for proposition in self.browse(cr, uid, ids):
            if proposition.state == 'invoiced':
                transaction_obj.prepare_move(cr, uid, [proposition.transaction_id.id], 'payment')

                skip_confirm = transaction_obj.get_skip_confirm(cr, uid, proposition.transaction_id)
                if not skip_confirm:
                    workflow.trg_validate(
                        uid, 'marketplace.proposition', proposition.id, 'proposition_invoiced_confirm', cr
                    )
                else:
                    workflow.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_invoiced_vote', cr)
                    self.test_vote(cr, uid, [proposition.id])
        return True

    def confirm(self, cr, uid, ids, *args):
        # Confirm that the receiver receive the currency, and go to the waiting vote state
        transaction_obj = self.pool.get('account.wallet.transaction')
        self.test_access_role(cr, uid, ids, 'is_receiver', *args)

        for proposition in self.browse(cr, uid, ids):
            if proposition.state == 'confirm':
                transaction_obj.prepare_move(cr, uid, [proposition.transaction_id.id], 'confirm')
                workflow.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_confirm_vote', cr)

        self.test_vote(cr, uid, ids)
        return True

    def reset_workflow(self, cr, uid, ids, *args):
        # Called by workflow, launch needed action depending of the next state and reset the workflow
        transaction_obj = self.pool.get('account.wallet.transaction')
        for proposition in self.browse(cr, uid, ids):
            state = proposition.state
            role_to_test = 'is_user'
            if state == 'rejected':
                role_to_test = 'is_announcer'
            elif state == 'paid':
                role_to_test = 'is_receiver'
            self.test_access_role(cr, uid, ids, role_to_test, *args)

            if state in ['cancel', 'rejected', 'paid']:
                workflow.trg_delete(uid, 'marketplace.proposition', proposition.id, cr)
                workflow.trg_create(uid, 'marketplace.proposition', proposition.id, cr)

            if state == 'paid':
                skip_confirm = transaction_obj.get_skip_confirm(cr, uid, proposition.transaction_id)
                if not skip_confirm:
                    workflow.trg_validate(
                        uid, 'marketplace.proposition', proposition.id, 'proposition_draft_confirm_refund', cr
                    )
                else:
                    workflow.trg_validate(
                        uid, 'marketplace.proposition', proposition.id, 'proposition_paid_cancel_through_draft', cr
                    )
        return True

    def create(self, cr, uid, vals, context=None):
        # Getting receiver_id from announcement when creating
        if 'announcement_id' in vals:
            announcement = self.pool.get('marketplace.announcement').browse(
                cr, uid, vals['announcement_id'], context=context
            )
            vals['receiver_id'] = announcement.partner_id.id
        res = super(MarketplaceProposition, self).create(cr, uid, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        # Security control the want_cancel checkbox and trigger the vote test
        if 'want_cancel_user' in vals or 'want_cancel_announcer' in vals:
            for proposition in self.browse(cr, uid, ids, context=context):
                if 'want_cancel_user' in vals and not proposition.is_user:
                    raise osv.except_osv(
                        _('Access error!'),
                        _("You need to have the role is_user to tick the cancel checkbox from user")
                    )
                #_logger.info('uid %s, proposition.is_announcer %s', uid, proposition.is_announcer)
                if 'want_cancel_announcer' in vals and not proposition.is_announcer:
                    raise osv.except_osv(
                        _('Access error!'),
                        _("You need to have the role is_announcer to tick the cancel checkbox from announcer")
                    )
        res = super(MarketplaceProposition, self).write(cr, uid, ids, vals, context=context)
        for proposition in self.browse(cr, uid, ids, context=context):
            if proposition.state == 'vote':
                self.test_vote(cr, uid, [proposition.id], context=context)
        return res


class AccountWalletTransaction(osv.osv):

    """
    Override transaction if proposition id an answer to a want, to exchange sender and receiver place
    """

    _inherit = 'account.wallet.transaction'

    def get_account_line(self, cr, uid, transaction, action, inv=False, name='Transaction', context=None):

        proposition_obj = self.pool.get('marketplace.proposition')
        proposition_ids = proposition_obj.search(cr, uid, [('transaction_id', '=', transaction.id)], context=context)
        for proposition in proposition_obj.browse(cr, uid, proposition_ids, context=context):
            if proposition.type == 'want':
                inv = True

        res = super(AccountWalletTransaction, self).get_account_line(
            cr, uid, transaction, action, inv=inv, name=name, context=context
        )
        return res


class ResPartner(osv.osv):

    """
    Add skills management in partner form, which are linked to category and tag
    """

    _inherit = 'res.partner'

    _columns = {
        'skill_category_ids': fields.many2many(
            'marketplace.announcement.category', 'res_partner_marketplace_category_rel',
            'partner_id', 'category_id', 'My skills (categories)'
        ),
        'skill_tag_ids': fields.many2many(
            'marketplace.tag', 'res_partner_marketplace_tag_rel', 'partner_id', 'tag_id', 'My skills (tags)'
        ),
    }


class IrAttachment(osv.osv):

    """
    Add the field name in ir.attachment, to easily retrieve the picture
    """

    _inherit = 'ir.attachment'

    _columns = {
        'binary_field': fields.char('Binary field', size=128)
    }
