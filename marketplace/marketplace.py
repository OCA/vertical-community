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


class marketplace_announcement_category(osv.osv):

    _name = 'marketplace.announcement.category'
    _description = 'Offers/Wants Categories'
    _inherit = ['vote.category','base.recursive.model']
    _columns = {
        'name': fields.char('Category Name', required=True, size=64, translate=True),
        'parent_id': fields.many2one('marketplace.announcement.category', 'Parent', select=True, ondelete='cascade'),
        'child_ids': fields.one2many('marketplace.announcement.category', 'parent_id', 'Childs'),
        'sequence': fields.integer('Sequence'),
        'tag_ids': fields.one2many('marketplace.tag', 'category_id', 'Tags'),
        'active': fields.boolean('Active', help="The active field allows you to hide the category without removing it."),
        'partner_ids': fields.many2many('res.partner', 'res_partner_marketplace_category_rel', 'category_id', 'partner_id', 'Partners'),
    }
    _defaults = {
        'active': 1,
    }


class marketplace_tag(osv.osv):

    _name = 'marketplace.tag'
    _description = 'Tag'
    _columns = {
        'name': fields.char('Tag', required=True, size=64, translate=True),
        'category_id': fields.many2one('marketplace.announcement.category', 'Category', ondelete='cascade', required=True),
        'partner_ids': fields.many2many('res.partner', 'res_partner_marketplace_tag_rel', 'tag_id', 'partner_id', 'Partners'),
    }
    _order = 'category_id, name'



class marketplace_announcement(osv.osv):

    def _is_user(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = False
            if announcement.user_id.id == uid:
                res[announcement.id] = True
        return res

    def _is_moderator(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        user_obj = self.pool.get('res.users')
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = False
            if user_obj.has_group(cr, uid, 'marketplace.group_marketplace_moderator'):
                res[announcement.id] = True
        return res

    def _get_company_name(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        company_obj = self.pool.get('res.company')
        company_ids = company_obj.search(cr, uid, [], context=context)
        company_name = company_obj.browse(cr, uid, company_ids, context=context)[0].name
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = company_name
        return res

    def _get_address(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = announcement.street or ''
            res[announcement.id] += ' ' + (announcement.street2 or '')
            res[announcement.id] += ', ' + (announcement.zip or '')
            res[announcement.id] += ' ' + (announcement.city or '')
            res[announcement.id] += ', ' + (announcement.state_id and announcement.state_id.name or '')
            res[announcement.id] += ' ' + (announcement.country_id and announcement.country_id.name or '')
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('res %s', res)

        return res


    def _get_qty_available(self, cr, uid, ids, prop, unknow_none, context=None):
        proposition_obj = self.pool.get('marketplace.proposition')
        res = {}
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = announcement.quantity
            proposition_ids = proposition_obj.search(cr, uid, [('announcement_id','=',announcement.id),('state','in',['accepted','invoiced','confirm','paid','confirm_refund'])], context=context)
            for proposition in proposition_obj.browse(cr, uid, proposition_ids, context=context):
                res[announcement.id] -= proposition.quantity
            if res[announcement.id] < 0 or announcement.infinite_qty:
                res[announcement.id] = 0
        return res

    def _get_binary_filesystem(self, cr, uid, ids, name, arg, context=None):
        """ Display the binary from ir.attachment, if already exist """
        res = {}
        attachment_obj = self.pool.get('ir.attachment')

        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = False
            attachment_ids = attachment_obj.search(cr, uid, [('res_model','=',self._name),('res_id','=',record.id),('binary_field','=',name)], context=context)
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('res %s', attachment_ids)
            if attachment_ids:
                img = attachment_obj.browse(cr, uid, attachment_ids, context=context)[0].datas
                _logger.info('res %s', img)
                res[record.id] = img
        return res

    def _set_binary_filesystem(self, cr, uid, id, name, value, arg, context=None):
        """ Create or update the binary in ir.attachment when we save the record """
        attachment_obj = self.pool.get('ir.attachment')

        attachment_ids = attachment_obj.search(cr, uid, [('res_model','=',self._name),('res_id','=',id),('binary_field','=',name)], context=context)
        if value:
            if attachment_ids:
                attachment_obj.write(cr, uid, attachment_ids, {'datas': value}, context=context)
            else:
                attachment_obj.create(cr, uid, {'res_model': self._name, 'res_id': id, 'name': 'Marketplace picture', 'binary_field': name, 'datas': value, 'datas_fname':'picture.jpg'}, context=context)
        else:
            attachment_obj.unlink(cr, uid, attachment_ids, context=context)



    _name = "marketplace.announcement"
    _description = 'Offer/Want'
    _inherit = ['mail.thread','vote.model']
    _inherits = {'vote.evaluated': "vote_evaluated_id"}
    _order = "create_date desc"
    _columns = {
        'name': fields.char('What', size=64, required=True),
        'type': fields.selection([
            ('offer','Offer'),
            ('want','Want'),
            ],'Type', readonly=True, required=True),
        'description': fields.text('Description'),
        'picture': fields.function(_get_binary_filesystem, fnct_inv=_set_binary_filesystem, type='binary', string='Picture'),
        'emergency': fields.boolean('Urgent?'),
        'expiration_date': fields.date('Expiry on'),
        'category_id': fields.many2one('marketplace.announcement.category', 'Category'),
        'tag_ids': fields.many2many('marketplace.tag', 'marketplace_announcement_tag_rel', 'announcement_id', 'tag_id', 'Tags'),
        'user_id': fields.many2one('res.users', 'Who', required=True, readonly=True),
        'infinite_qty': fields.boolean('Unlimited'), #seulement sur offers
        'quantity': fields.float('Quantity', digits_compute= dp.get_precision('Product Unit of Measure')),
        'quantity_available': fields.function(_get_qty_available, type="float", string="Available", digits_compute= dp.get_precision('Product Unit of Measure'), readonly=True),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', ondelete='set null'),
#        'currency_ids': fields.one2many('marketplace.announcement.currency', 'announcement_id', 'Currencies'),
        'currency_ids': fields.one2many('marketplace.announcement.currency', 'announcement_id', 'Currencies'),
#        'community_currency_accepted': fields.boolean('Accept community currency?'),
#        'community_price_unit': fields.float('Wished unit price', digits_compute= dp.get_precision('Product Price')),
#        'community_currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
#        'community_company_commission': fields.float('% company commission community', digits_compute= dp.get_precision('Product Price')),
#        'real_currency_accepted': fields.boolean('Accept real currency?'),
#        'real_price_unit': fields.float('Wished unit price', digits_compute= dp.get_precision('Product Price')),
#        'real_currency_id': fields.many2one('res.currency', 'Currency', readonly=True),
#        'real_company_commission': fields.float('% company commission real', digits_compute= dp.get_precision('Product Price')),
        'delivery_date': fields.date('When'),
        'create_date': fields.datetime('Create date'),
        'publish_date': fields.datetime('Published on'),
        'proposition_ids': fields.one2many('marketplace.proposition', 'announcement_id', 'Propositions'),
        'from_company': fields.boolean('From company?'),
        'company_name': fields.function(_get_company_name, type="char", size=64, string="Who"),
        'address': fields.function(_get_address, type="char", size=512, string="Where", store=True, readonly=True),
        'street': fields.char('Street', size=128),
        'street2': fields.char('Street2', size=128),
        'zip': fields.char('Zip', change_default=True, size=24),
        'city': fields.char('City', size=128),
        'state_id': fields.many2one("res.country.state", 'State'),
        'country_id': fields.many2one('res.country', 'Country'),
        'is_user': fields.function(_is_user, type="boolean", string="Is user?"),
        'is_moderator': fields.function(_is_user, type="boolean", string="Is moderator?"),
        'vote_evaluated_id': fields.many2one('vote.evaluated', 'Evaluated', ondelete="cascade", required=True),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Published'),
            ('done','Closed'),
            ('cancel','Cancelled'),
            ],'Status', readonly=True, required=True),

    }

#    def _default_community_currency(self, cr, uid, context=None):
#        return self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_community_currency_id')

#    def _default_real_currency(self, cr, uid, context=None):
#        return self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_real_currency_id')

#    def _default_community_company_commission(self, cr, uid, context=None):
#        return self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'marketplace_community_percent_company')

#    def _default_real_company_commission(self, cr, uid, context=None):
#        return self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'marketplace_real_percent_company')

    def _get_uom_id(self, cr, uid, *args):
        try:
            proxy = self.pool.get('ir.model.data')
            result = proxy.get_object_reference(cr, uid, 'product', 'product_uom_unit')
            return result[1]
        except Exception, ex:
            return False

    def _default_currency_ids(self, cr, uid, context=None):
        proxy = self.pool.get('ir.model.data')
        config = proxy.get_object(cr, uid, 'marketplace', 'marketplace_settings')
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('config :  %s', config)

        vals = {}
        vals['price_unit'] = 1.0
        vals['currency_id'] = config.default_currency_id.id
        vals['company_commission'] = 0.0
        return [(0, 0, vals)]

    _defaults = {
        'type': 'offer',
        'state': 'draft',
        'user_id': lambda s, cr, u, c: u,
        'currency_ids': _default_currency_ids,
#       'community_currency_accepted': True,
#        'community_price_unit': 1.0,
#        'community_currency_id': _default_community_currency,
#        'community_company_commission': _default_community_company_commission,
#        'real_currency_accepted': True,
#        'real_price_unit': 1.0,
#        'real_currency_id': _default_real_currency,
#        'real_company_commission': _default_real_company_commission,
        'quantity': 1.0,
        'uom_id': _get_uom_id,
        'is_user': True,
    }

    def onchange_author(self, cr, uid, ids, from_company, user_id, context=None):
        user_obj = self.pool.get('res.users')
        company_obj = self.pool.get('res.company')
        if from_company:
            company_ids = company_obj.search(cr, uid, [], context=context)
            partner = company_obj.browse(cr, uid, company_ids, context=context)[0].partner_id
        else:
            partner = user_obj.browse(cr, uid, [user_id], context=context)[0].partner_id

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


    def test_is_user(self, cr, uid, ids, *args):
        res = self._is_user(cr, uid, ids, {}, {})
        for announcement_id in ids:
            if not res[announcement_id] and not self.pool.get('res.users').has_group(cr, uid, 'marketplace.group_marketplace_moderator'):
                raise osv.except_osv(_('Access error!'),_("Only the author of the announcement or a moderator can change the state of the announce!"))
        return True

    def publish(self, cr, uid, ids, *args):
        for announcement in self.browse(cr, uid, ids):
            fields = {'state':'open'}
            if not announcement.publish_date:
                fields['publish_date'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.write(cr, uid, [announcement.id], fields)

    def reset_workflow(self, cr, uid, ids, *args):

        self.test_is_user(cr, uid, ids, *args)
 
        wf_service = netsvc.LocalService("workflow")
        for announcement in self.browse(cr, uid, ids):
            state = announcement.state
            self.write(cr, uid, [announcement.id], {'state':'draft'})
            wf_service.trg_delete(uid, 'marketplace.announcement', announcement.id, cr)
            wf_service.trg_create(uid, 'marketplace.announcement', announcement.id, cr)
            if state == 'done':
                wf_service.trg_validate(uid, 'marketplace.announcement', announcement.id, 'announcement_draft_open', cr)
        return True

    def add_proposition(self, cr, uid, ids, context):

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

#draft->published
#published->cancelled
#cancelled->draft
#published->close
#close->published
#Impossible de supprimer annonce avec proposition, on ne peut voir que les annonces publiees de tous ou ses annonces
#Autoclose l'annonce a date expiration, autofill with today + jours from configuration
#Acceptation d'une proposition diminue quantity sur l'annonce. Si 0, autoclose.

#class marketplace_announcement_currency(osv.osv):

#    _name = 'marketplace.announcement.currency'
#    _description = 'Currency'

#    def _get_subtotal(self, cr, uid, ids, prop, unknow_none, context=None):
#        res = {}
#        if context is None:
#            context = {}
#        for currency in self.browse(cr, uid, ids, context=context):
#            res[currency.id] = 1.0
#            if currency.announcement_id:
#                res[currency.id] = currency.announcement_id.quantity * currency.price_unit
#            elif currency.proposition_id:
#                res[currency.id] = currency.proposition_id.quantity * currency.price_unit
#            import logging
#            _logger = logging.getLogger(__name__)
#            _logger.info('res %s', res)
#
#    _columns = {
#        'announcement_id': fields.many2one('marketplace.announcement', 'Announcement'),
#        'proposition_id': fields.many2one('marketplace.proposition', 'Proposition'),
#        'price_unit': fields.float('Wished unit price', required=True, digits_compute= dp.get_precision('Product Price')),
#        'currency_id': fields.many2one('res.currency', 'Currency', domain=[('marketplace_currency', '=', True)], required=True),
#        'company_commission': fields.float('% company commission', digits_compute= dp.get_precision('Product Price')),
#        'subtotal': fields.function(_get_subtotal, string='Subtotal', digits_compute= dp.get_precision('Account')),
#    }


class marketplace_proposition(osv.osv):

    def _get_vote_voters(self, cr, uid, ids, name, args, context=None):
        res = {}

        partner_ids = self.pool.get('res.partner').search(cr, uid, [('user_ids','!=',False)], context=context)
        for record in self.browse(cr, uid, ids, context=context):
            res[record.id] = [(6, 0, [record.user_id.partner_id.id, record.announcement_id.user_id.partner_id.id])]
        return res


    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        wf_service = netsvc.LocalService("workflow")
        res = {}
        for proposition in self.browse(cr, uid, ids):
            res[proposition.id] = {}
            res[proposition.id]['is_user'] = False
            res[proposition.id]['is_announcer'] = False
            res[proposition.id]['is_dispute'] = False
            res[proposition.id]['is_moderator'] = False
            res[proposition.id]['is_invoicer'] = False
            res[proposition.id]['is_payer'] = False
            res[proposition.id]['is_moderator_or_aggree'] = False
            if proposition.user_id.id == uid:
                res[proposition.id]['is_user'] = True
                res[proposition.id]['is_dispute'] = True
                if proposition.type == 'offer':
                    res[proposition.id]['is_payer'] = True
                else:
                    res[proposition.id]['is_invoicer'] = True
            if proposition.announcement_id.user_id.id == uid:
                res[proposition.id]['is_announcer'] = True
                res[proposition.id]['is_dispute'] = True
                if proposition.type != 'offer':
                    res[proposition.id]['is_payer'] = True
                else:
                    res[proposition.id]['is_invoicer'] = True
            if self.pool.get('res.users').has_group(cr, uid, 'marketplace.group_marketplace_moderator'):
                res[proposition.id]['is_moderator'] = True
                res[proposition.id]['is_moderator_or_aggree'] = True
            if res[proposition.id]['is_dispute'] and proposition.want_cancel_user and proposition.want_cancel_announcer:
                res[proposition.id]['is_moderator_or_aggree'] = True

#            if proposition.state == 'confirm' and proposition.skip_confirm:
#                import logging
#                _logger = logging.getLogger(__name__)
#                _logger.info('test !!!!')
#                self.write(cr, uid, [proposition.id], {'skip_confirm': False}, context=context)
#                wf_service.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_confirm_paid', cr)

        return res

    _name = 'marketplace.proposition'
    _description = 'Proposition'
    _inherits = {'account.centralbank.transaction': "transaction_id"}
    _inherit = ['mail.thread','vote.model']
    _vote_category_field = 'category_id'
    _vote_category_model = 'marketplace.announcement.category'
    _columns = {
        'announcement_id': fields.many2one('marketplace.announcement', 'What', required=True),
        'name': fields.related('announcement_id', 'name', type='char', string='Name', store=True),
        'type': fields.related('announcement_id', 'type', type='char', string='Type', store=True),
        'uom_id': fields.related('announcement_id', 'uom_id', type='many2one', relation='product.uom', string='Unit of Measure', ondelete='set null', readonly=True),
        'description_announcement_id': fields.many2one('marketplace.announcement', 'Link to announcement proposition'), #only the user announcement are displayed and countertype (offer if want annonce or want if offer annonce
        'description': fields.text('Detail'),
        'category_id': fields.related('announcement_id', 'category_id', type="many2one", relation="marketplace.announcement.category", string='Category'),
        'want_cancel_user': fields.boolean('(Replyer) I want to cancel the transaction'),
        'want_cancel_announcer': fields.boolean('(Announcer) I want to cancel the transaction'),
        'call_moderator_user': fields.boolean('(Replyer) I want to call moderator?'),
        'call_moderator_announcer': fields.boolean('(Announcer) I want to Call moderator?'),
        'reservation_id': fields.many2one('account.move', 'Reservation move'),
        'invoice_id': fields.many2one('account.move', 'Invoice move'),
        'payment_id': fields.many2one('account.move', 'Payment move'),
        'confirm_id': fields.many2one('account.move', 'Confirmation move'),
        'already_published': fields.boolean('Already published?'),
        'already_accepted': fields.boolean('Already accepted?'),
        'vote_voters': fields.function(_get_vote_voters, type='many2many', obj='res.partner', string='Voters'),
        'is_user': fields.function(_get_user_role, type="boolean", string="Is user?", multi='role'),
        'is_announcer': fields.function(_get_user_role, type="boolean", string="Is announcer?", multi='role'),
        'is_dispute': fields.function(_get_user_role, type="boolean", string="Is dispute?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'is_invoicer': fields.function(_get_user_role, type="boolean", string="Is invoicer?", multi='role'),
        'is_payer': fields.function(_get_user_role, type="boolean", string="Is payer?", multi='role'),
        'is_moderator_or_aggree': fields.function(_get_user_role, type="boolean", string="Is moderator or aggree?", multi='role'),
        'skip_confirm': fields.boolean('Skip confirm'),
        'state': fields.selection([
            ('draft','Draft'),
            ('open','Open'),
            ('accepted','Accepted'),
            ('rejected','Rejected'),
            ('invoiced','Invoiced'),
            ('confirm','Payment confirmation'),
            ('vote','Waiting for votes'),
            ('paid','Paid'),
            ('confirm_refund','Refund payment confirmation'),
            ('cancel','Cancelled'),
            ],'Status', readonly=True, required=True),
    }

#    def _default_community_price_unit(self, cr, uid, context=None):
#        if context is None:
#            context = {}
#        price = 1.0
#        if context.get('default_announcement_id'):
#            price = self.pool.get('marketplace.announcement').browse(cr, uid, [context.get('default_announcement_id')], context=context)[0].community_price_unit
#        return price

#    def _default_real_price_unit(self, cr, uid, context=None):
#        if context is None:
#            context = {}
#        price = 1.0
#        if context.get('default_announcement_id'):
#            price = self.pool.get('marketplace.announcement').browse(cr, uid, [context.get('default_announcement_id')], context=context)[0].real_price_unit
#        return price


#    def _default_community_currency(self, cr, uid, context=None):
#        if context is None:
#            context = {}
#        currency_id = self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'marketplace_community_currency_id')
#        if context.get('default_announcement_id'):
#            currency_id = self.pool.get('marketplace.announcement').browse(cr, uid, [context.get('default_announcement_id')], context=context)[0].community_currency_id.id
#        return currency_id

#    def _default_real_currency(self, cr, uid, context=None):
#        if context is None:
#            context = {}
#        currency_id = self.pool.get('ir.config_parameter').get_param(cr, SUPERUSER_ID, 'marketplace_real_currency_id')
#        if context.get('default_announcement_id'):
#            currency_id = self.pool.get('marketplace.announcement').browse(cr, uid, [context.get('default_announcement_id')], context=context)[0].real_currency_id.id
#        return currency_id

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


    _defaults = {
        'currency_ids': _default_currency_ids,
    }

    def _get_evaluated(self, cr, uid, id, partner_id, context=None):
        proposition = self.browse(cr, uid, id, context=context)
        partner_evaluated_id = proposition.user_id.partner_id.vote_evaluated_id.id
        if proposition.user_id.partner_id.id == partner_id:
            res = [proposition.announcement_id.user_id.partner_id.vote_evaluated_id.id, proposition.announcement_id.vote_evaluated_id.id]
        else:
            res = [proposition.user_id.partner_id.vote_evaluated_id.id]
        _logger.info('res %s', res)
        return res


    def test_vote(self, cr, uid, ids, context=None):
        wf_service = netsvc.LocalService("workflow")
        vote_obj = self.pool.get('vote.vote')

        for proposition in self.browse(cr, uid, ids, context=context):
            vote_user = False
            vote_announcer = False
            user_partner_id = proposition.user_id.partner_id.id
            announcer_partner_id = proposition.announcement_id.user_id.partner_id.id
            vote_ids = vote_obj.search(cr, uid, [('model','=','marketplace.proposition'), ('res_id','=',proposition.id), ('partner_id','in',[user_partner_id,announcer_partner_id])], context=context)
            for vote in vote_obj.browse(cr, uid, vote_ids, context=context):
                if vote.partner_id.id == user_partner_id:
                    vote_user = vote
                if vote.partner_id.id == announcer_partner_id:
                    vote_announcer = vote

            if vote_user and vote_user.is_complete and vote_announcer and vote_announcer.is_complete:
                wf_service.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_vote_paid', cr)


    def test_access_role(self, cr, uid, ids, role_to_test, *args):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test')

        res = self._get_user_role(cr, uid, ids, {}, {})

        for proposition in self.browse(cr, uid, ids):
            role = res[proposition.id]
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('Role : %s, role to test : %s', role, role_to_test)

            if not role[role_to_test] and not role['is_moderator']:
                raise osv.except_osv(_('Access error!'),_("Only the author of the announcement or a moderator can change the state of the announce!"))
        return True


    def change_state(self, cr, uid, ids, new_state, *args):
        wf_service = netsvc.LocalService("workflow")
        transaction_obj = self.pool.get('marketplace.transaction')
        partner_obj = self.pool.get('res.partner')
        for proposition in self.browse(cr, uid, ids):
            fields = {'state':new_state}
            if new_state == 'open':
                if proposition.quantity > proposition.announcement_id.quantity_available and not proposition.announcement_id.infinite_qty:
                    raise osv.except_osv(_('Access error!'),_("There is not enough quantity available!"))
                fields['already_published'] = True
            if new_state == 'accepted':
                if proposition.type == 'offer':
                    payer = proposition.user_id.partner_id
                else:
                    payer = proposition.announcement_id.user_id.partner_id
                balance = partner_obj.get_marketplace_balance(cr, uid, [payer.id])[payer.id]
                import logging
                _logger = logging.getLogger(__name__)
                _logger.info('balance : %s, payer: %s', balance, payer)
                for currency in proposition.currency_ids:
                    if (balance[currency.currency_id.id]['available'] - currency.subtotal) < balance[currency.currency_id.id]['limit']:
                        raise osv.except_osv(_('Limit error!'),_("Not enough amount available. Currency : %s, Amount needed : %s, Limit : %s") % (currency.currency_id.symbol, balance[currency.currency_id.id]['available'] - currency.subtotal, balance[currency.currency_id.id]['limit']))
                self.prepare_move(cr, uid, [proposition.id], 'reservation')
                fields['already_accepted'] = True
            if new_state == 'invoiced':
                self.prepare_move(cr, uid, [proposition.id], 'invoice')
            if new_state == 'confirm':
                self.prepare_move(cr, uid, [proposition.id], 'payment')
            if new_state == 'vote':
                self.prepare_move(cr, uid, [proposition.id], 'confirm')
                self.test_vote(cr, uid, [proposition.id])
            if new_state == 'cancel':
                transaction_obj.refund(cr, uid, [proposition.transaction_id.id], ['reservation','invoice','payment','confirm'], 'marketplace.proposition')
            import logging
            _logger = logging.getLogger(__name__)
            _logger.info('fields : %s', fields)
            self.write(cr, SUPERUSER_ID, [proposition.id], fields)

            if new_state == 'confirm':
                config_currency_obj = self.pool.get('marketplace.config.currency')

                currency_ids = []
                for currency in proposition.currency_ids:
                    currency_ids.append(currency.currency_id.id)
                config_currency_ids = config_currency_obj.search(cr, uid, [('currency_id', 'in', currency_ids)])

                import logging
                _logger = logging.getLogger(__name__)
                _logger.info("config_currency_ids : %s", config_currency_ids)


                skip_confirm = True
                for config_currency in config_currency_obj.browse(cr, uid, config_currency_ids):
                    if config_currency.external_currency:
                        skip_confirm = False
                if skip_confirm:
                    _logger.info("[skip_config: %s", skip_confirm)
                    self.write(cr, uid, [proposition.id], {'skip_confirm': True})
                    wf_service.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_confirm_paid', cr)

            

    def reset_workflow(self, cr, uid, ids, *args):
        import logging
        _logger = logging.getLogger(__name__)
        _logger.info('test reset')

        wf_service = netsvc.LocalService("workflow")
        for proposition in self.browse(cr, uid, ids):
            state = proposition.state
            role_to_test = 'is_user'
            if state == 'rejected':
                role_to_test = 'is_announcer'
            elif state == 'paid':
                role_to_test = 'is_invoicer'
            self.test_access_role(cr, uid, ids, role_to_test, *args)

            wf_service.trg_delete(uid, 'marketplace.proposition', proposition.id, cr)
            wf_service.trg_create(uid, 'marketplace.proposition', proposition.id, cr)

            if state == 'paid':
                wf_service.trg_validate(uid, 'marketplace.proposition', proposition.id, 'proposition_paid_confirm_refund', cr)
        return True

    def get_debit_credit_partner(self, cr, uid, debit_object, credit_object, context=None):
        return {
            'debit': debit_object.user_id.partner_id,
            'credit': credit_object.user_id.partner_id,
        }

    def write(self, cr, uid, ids, vals, context=None):
        res = super(marketplace_proposition, self).write(cr, uid, ids, vals, context=context)
        for proposition in self.browse(cr, uid, ids, context=context):
            if proposition.state == 'vote':
                self.test_vote(cr, uid, [proposition.id], context=context)
        return res



#    def reserve(self, cr, uid, ids, *args):
#        journal_obj = self.pool.get('account.journal')
#        move_obj = self.pool.get('account.move')
#        company_obj = self.pool.get('res.company')
#        config_obj = self.pool.get('ir.config_parameter')
#
#        date = datetime.now().date().strftime("%Y-%m-%d")
#
#        context = {}
#        company_id = company_obj._company_default_get(cr, uid)
#        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id
#
#        for proposition in self.browse(cr, uid, ids):
#
#            ref = proposition.announcement_id.name
#            journal_id = config_obj.get_param(cr, uid, 'marketplace_journal_id')
#            move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
#            move['marketplace_proposition_id'] = proposition.id
#            move['marketplace_action'] = 'reserve'
#            move_id = move_obj.create(cr, uid, move)
#
#            lines = self.get_account_line(cr, uid, proposition, 'reserve', 'base', context=context)
#            import logging
#            _logger = logging.getLogger(__name__)
#            _logger.info('lines: %s',lines)
#
#            move_obj.write(cr, uid, [move_id], {'line_id': lines})
#            move_obj.post(cr, uid, [move_id])
#            self.write(cr, uid, [proposition.id], {'reservation_id': move_id})


#    def invoice(self, cr, uid, ids, *args):
#        journal_obj = self.pool.get('account.journal')
#        move_obj = self.pool.get('account.move')
#        company_obj = self.pool.get('res.company')
#        config_obj = self.pool.get('ir.config_parameter')
#
#        date = datetime.now().date().strftime("%Y-%m-%d")
#
#        context = {}
#        company_id = company_obj._company_default_get(cr, uid)
#        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id
#
#        for proposition in self.browse(cr, uid, ids):
#
#            ref = proposition.announcement_id.name
#            journal_id = config_obj.get_param(cr, uid, 'marketplace_journal_id')
#            move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
#            move['marketplace_proposition_id'] = proposition.id
#            move['marketplace_action'] = 'invoice'
#            move_id = move_obj.create(cr, uid, move)
#
#            lines = self.get_account_line(cr, uid, proposition, 'invoice', 'base', context=context)
#                if proposition.announcement_id.community_company_commission:
#                    lines = self.get_account_line(cr, uid, lines, proposition, 'community', 'invoice', 'company_com', context=context)

            #TODO move in group module
#            if proposition.community_price_unit and proposition.announcement_id.community_group_commission:
#                lines = self.get_account_line(cr, uid, lines, proposition, 'community', 'invoice', 'group_com', context=context)
#            if proposition.real_price_unit and proposition.announcement_id.real_company_commission:
#                lines = self.get_account_line(cr, uid, lines, proposition, 'real', 'invoice', 'group_com', context=context)

#            move_obj.write(cr, uid, [move_id], {'line_id': lines})
#            move_obj.post(cr, uid, [move_id])
#            self.write(cr, uid, [proposition.id], {'invoice_id': move_id})



    def prepare_move(self, cr, uid, ids, action, context=None):
        wf_service = netsvc.LocalService("workflow")
        journal_obj = self.pool.get('account.journal')
        move_obj = self.pool.get('account.move')
        company_obj = self.pool.get('res.company')
        transaction_obj = self.pool.get('marketplace.transaction')
        config_obj = self.pool.get('ir.config_parameter')

        date = datetime.now().date().strftime("%Y-%m-%d")

        context = {}
        company_id = company_obj._company_default_get(cr, uid)
        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id

        for proposition in self.browse(cr, uid, ids):

            lines = transaction_obj.get_account_line(cr, uid, proposition, action, 'base', context=context)

            if lines:
                ref = proposition.announcement_id.name
                journal_id = config_obj.get_param(cr, uid, 'marketplace_journal_id')
                move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
                move['marketplace_transaction_id'] = proposition.transaction_id.id
                move['marketplace_action'] = action
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
                self.write(cr, uid, [proposition.id], {action + '_id': move_id})
                if proposition.reservation_id:
                    transaction_obj.reconcile(cr, uid, [proposition.reservation_id.id, move_id], context=context)



#    def confirm(self, cr, uid, ids, *args):
#        journal_obj = self.pool.get('account.journal')
#        move_obj = self.pool.get('account.move')
#        company_obj = self.pool.get('res.company')
#        config_obj = self.pool.get('ir.config_parameter')
#
#        date = datetime.now().date().strftime("%Y-%m-%d")
#
#        context = {}
#        company_id = company_obj._company_default_get(cr, uid)
#        context['company_currency'] = company_obj.browse(cr, uid, [company_id])[0].currency_id.id
#
#        for proposition in self.browse(cr, uid, ids):
#
#            lines = self.get_account_line(cr, uid, proposition, 'confirm', 'base', context=context)
#
#            if lines:
#                ref = proposition.announcement_id.name
#                journal_id = config_obj.get_param(cr, uid, 'marketplace_journal_id')
#                move = move_obj.account_move_prepare(cr, uid, journal_id, date=date, ref=ref)
#                move['marketplace_proposition_id'] = proposition.id
#                move['marketplace_action'] = 'confirm'
#                move_id = move_obj.create(cr, uid, move)
#
#                move_obj.write(cr, uid, [move_id], {'line_id': lines})
#                move_obj.post(cr, uid, [move_id])
#                self.write(cr, uid, [proposition.id], {'confirmation_id': move_id})
#                self.reconcile(cr, uid, [proposition.reservation_id.id, move_id], context=context)


#draft->open author proposition
#open->accepted autor annoucement
#open->refused author annoucement
#refused->draft author announcement
#draft->cancelled open->cancelled cancel->draft author proposition
#accepted->dispute both author
#dispute->accepted/refused moderator
#accepted->paid author announcement if want of author proposition if offer
#La suppression est autorise aux status draft et cancel, uniquement par l'authur de la propositionA ce stade, seul l'auteur de la proposition peut les voir.

class account_move(osv.osv):

    _inherit = 'account.move'

    _columns = {
        'marketplace_transaction_id': fields.many2one('marketplace.transaction', 'Transaction'),
        'marketplace_action': fields.selection([
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


    _columns = {
        'skill_category_ids': fields.many2many('marketplace.announcement.category', 'res_partner_marketplace_category_rel', 'partner_id', 'category_id', 'My skills (category)'),
        'skill_tag_ids': fields.many2many('marketplace.tag', 'res_partner_marketplace_tag_rel', 'partner_id', 'tag_id', 'My skills (tags)'),
    }

