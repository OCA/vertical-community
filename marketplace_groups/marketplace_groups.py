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


class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'is_group': fields.boolean('Is a group')
    }

class mail_group(osv.osv):

    _inherit = 'mail.group'

    def _can_have_commission(self, cr, uid, ids, prop, unknow_none, context=None):
        res = {}
        can_have_commission = self.pool.get('ir.config_parameter').get_param(cr, uid, 'marketplace_group_commission')
        for announcement in self.browse(cr, uid, ids):
            res[announcement.id] = False
            if can_have_commission:
                res[announcement.id] = True
        return res

    _columns = {
        'partner_id': fields.many2one('res.partner', 'Partner', ondelete='cascade'),
        'marketplace': fields.boolean('Can be used in marketplace?'),
        'community_percent': fields.float('% Community', digits_compute= dp.get_precision('Product Price')),
        'real_percent': fields.float('% Real', digits_compute= dp.get_precision('Product Price')),
        'can_have_commission': fields.function(_can_have_commission, type="boolean", string="Can have commission?"),
    }

    def create(self, cr, uid, vals, context=None):
        partner_obj = self.pool.get('res.partner')
        vals['partner_id'] = partner_obj.create(cr, uid, {'name':vals['name'], 'is_group':True}, context=context)
        res = super(mail_group, self).create(cr, uid, vals, context=context)
        return res

    def write(self, cr, uid, ids, vals, context=None):
        if 'name' in vals:
            partner_obj = self.pool.get('res.partner')
            for group in self.browse(cr, uid, ids, context=context):
                if group.partner_id:
                    partner_obj.write(cr, uid, [group.partner_id.id], {'name':vals['name']}, context=context)
        res = super(mail_group, self).write(cr, uid, ids, vals, context=context)
        return res

    def unlink(self, cr, uid, ids, context=None):
        partner_obj = self.pool.get('res.partner')
        for group in self.browse(cr, uid, ids, context=context):
            if group.partner_id:
                partner_obj.unlink(cr, uid, [group.partner_id.id], context=context)
        res = super(mail_group, self).unlink(cr, uid, ids, context=context)
        return res


class marketplace_announcement(osv.osv):

    _inherit = 'marketplace.announcement'

    def _is_user(self, cr, uid, ids, prop, unknow_none, context=None):
        res = super(marketplace_announcement, self)._is_user(cr, uid, ids, prop, unknow_none, context=context)
        for announcement in self.browse(cr, uid, ids):
            if announcement.from_group:
                res[announcement.id] = False
                if uid in [u.id for u in announcement.group_id.manager_ids]:
                    res[announcement.id] = True
        return res


    _columns = {
        'context_group_ids': fields.many2many('mail.group', 'marketplace_announcement_group_rel', 'announcement_id', 'group_id', 'Groups'),
        'from_group': fields.boolean('From group?'),
        'group_id': fields.many2one('mail.group', 'Group'),
        'community_group_commission': fields.float('% group commission community', digits_compute= dp.get_precision('Product Price')),
        'real_group_commission': fields.float('% group commission real', digits_compute= dp.get_precision('Product Price')),
        'is_user': fields.function(_is_user, type="boolean", string="Is user?"),
    }


class marketplace_proposition(osv.osv):

    _inherit = 'marketplace.proposition'

    def _get_user_role(self, cr, uid, ids, prop, unknow_none, context=None):
        res = super(marketplace_proposition, self)._get_user_role(cr, uid, ids, prop, unknow_none, context=context)
        for proposition in self.browse(cr, uid, ids):
            if proposition.from_group or proposition.announcement_id.from_group:
                res[proposition.id]['is_dispute'] = False
            if proposition.from_group:
                res[proposition.id]['is_user'] = False
                if proposition.type == 'offer':
                    res[proposition.id]['is_payer'] = False
                if uid in [u.id for u in proposition.group_id.manager_ids]:
                    res[proposition.id]['is_user'] = True
                    res[proposition.id]['is_dispute'] = True
                    if proposition.type == 'offer':
                        res[proposition.id]['is_payer'] = True
            if proposition.announcement_id.from_group:
                res[proposition.id]['is_announcer'] = False
                if proposition.type != 'offer':
                    res[proposition.id]['is_payer'] = False
                if uid in [u.id for u in proposition.announcement_id.group_id.manager_ids]:
                    res[proposition.id]['is_announcer'] = True
                    res[proposition.id]['is_dispute'] = True
                    if proposition.type != 'offer':
                        res[proposition.id]['is_payer'] = True
        return res


    _columns = {
        'from_group': fields.boolean('From group?'),
        'group_id': fields.many2one('mail.group', 'Group'),
        'is_user': fields.function(_get_user_role, type="boolean", string="Is user?", multi='role'),
        'is_announcer': fields.function(_get_user_role, type="boolean", string="Is announcer?", multi='role'),
        'is_dispute': fields.function(_get_user_role, type="boolean", string="Is dispute?", multi='role'),
        'is_moderator': fields.function(_get_user_role, type="boolean", string="Is moderator?", multi='role'),
        'is_payer': fields.function(_get_user_role, type="boolean", string="Is payer?", multi='role'),
    }

    def get_debit_credit_partner(self, cr, uid, debit_object, credit_object):

        res = super(marketplace_proposition, self).get_debit_credit_partner(cr, uid, debit_object, credit_object)

        if debit_object.from_group:
            res['debit'] = debit_object.group_id.partner_id
        if credit_object.from_group:
            res['credit'] = credit_object.group_id.partner_id

        return res
