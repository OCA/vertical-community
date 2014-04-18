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

class res_partner(osv.osv):

    _inherit = 'res.partner'

    _columns = {
        'presentation': fields.text('Presentation'),
    }

class mail_group(osv.osv):

    _inherit = 'mail.group'

    _columns = {
        'manager_ids': fields.many2many('res.users', 'mail_group_res_users', 'group_id', 'user_id', 'Managers', domain=[('committee','=',True)]),
    }


class res_users(osv.osv):

    _inherit = 'res.users'

    _columns = {
        'committee': fields.boolean('Committee?'),
        'moderator': fields.boolean('Moderator?'),
    }

    def write(self, cr, uid, ids, values, context=None):

        model  = self.pool.get('ir.model.data')
        group_obj = self.pool.get('res.groups')

        if 'moderator' in values:
            if values['moderator']:
                values['committee'] = True

        if 'committee' in values:
            if values['committee']:
                moderator_group_id = model.get_object(cr, uid, 'mail_groups_management', 'group_mail_committee').id
                for id in ids:
                    group_obj.write(cr, uid, [moderator_group_id], {'users': [(4, id)]}, context=context)
            else:
                group_ids = group_obj.search(cr, uid, [('name', 'not in',['Portal','Anonymous'])], context=context)
                base_group_id = model.get_object(cr, uid, 'base', 'group_user').id
                for id in ids:
                    group_obj.write(cr, uid, group_ids, {'users': [(3, id)]}, context=context)
                    group_obj.write(cr, uid, [base_group_id], {'users': [(4, id)]}, context=context)
        if 'moderator' in values:
            if values['moderator']:
                moderator_group_id = model.get_object(cr, uid, 'membership_users', 'group_membership_moderator').id
                for id in ids:
                    group_obj.write(cr, uid, [moderator_group_id], {'users': [(4, id)]}, context=context)
            else:
                group_ids = group_obj.search(cr, uid, [('name', 'not in',['Portal','Anonymous'])], context=context)
                base_group_id = model.get_object(cr, uid, 'base', 'group_user').id
                for user in self.browse(cr, uid, ids, context=context):
                    if user.committee and not 'committee' in values or 'committee' in values and values['committee']:
                        base_group_id = model.get_object(cr, uid, 'mail_groups_management', 'group_mail_committee').id
                    group_obj.write(cr, uid, group_ids, {'users': [(3, user.id)]}, context=context)
                    group_obj.write(cr, uid, [base_group_id], {'users': [(4, user.id)]}, context=context)

        res = super(res_users, self).write(cr, uid, ids, values, context=context)

        return res
